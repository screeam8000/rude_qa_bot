import logging
import random
from pathlib import Path
from typing import Dict, Any, List

import yaml
from telebot.types import InlineKeyboardButton, User, InlineKeyboardMarkup, Message
from yaml.scanner import ScannerError

from const import GreetingDefaultSettings
from dto import GreetingQuestionDto, NewbieDto
from error import UserAlreadyInStorageError, UserNotFoundInStorageError, UserStorageUpdateError, GreetingsLoadError


class NewbieStorage:
    _storage: Dict[Any, NewbieDto]

    def __init__(self, logger: logging.Logger):
        self._storage = dict()
        self._logger = logger

    def __iter__(self):
        for key, value in self._storage.items():
            yield value

    def add(self, user: User, timeout: int, question: GreetingQuestionDto):
        newbie = NewbieDto(user=user, timeout=timeout, question=question)
        self._logger.debug(f'Trying to add user @{user.username} into newbie list')
        if user.id in self._storage:
            self._logger.warning(f'Can not add! User @{user.username} already in newbie list.')
            raise UserAlreadyInStorageError()

        self._storage.update({user.id: newbie})

    def remove(self, user: User):
        try:
            self._logger.debug(f'Trying to remove newbie {user} from list')
            del self._storage[user.id]
        except KeyError:
            self._logger.warning(f'Can not remove! User @{user.username} not found in newbie list!')

    def update(self, user: User, greeting: Message):
        self._logger.debug(f'Trying to update greeting {greeting} for newbie @{user.username}')
        try:
            current_newbie = self.get(user)
        except UserNotFoundInStorageError:
            raise UserStorageUpdateError()
        self._storage[user.id] = NewbieDto(
            user=current_newbie.user,
            timeout=current_newbie.timeout,
            question=current_newbie.question,
            greeting=greeting,
        )

    def get(self, user: User) -> NewbieDto:
        try:
            return self._storage[user.id]
        except KeyError:
            self._logger.error(f'Can not get! User @{user.username} not found in newbie list.')
            raise UserNotFoundInStorageError()

    def get_user_list(self) -> list:
        return list(self._storage.keys())


class QuestionLoader:
    _logger = logging.getLogger('greetings_file_loader')  # Logger from baseConfig settings

    @staticmethod
    def load_questions() -> List[GreetingQuestionDto]:
        """
        This method loads greeting questions list from yaml file
        Note: dynamical reload can be added here
        :return: List[GreetingQuestionDto] - list with greeting question dto's
        """
        result = QuestionLoader._set_default_greeting()
        try:
            result = QuestionLoader._load_questions_from_file()
        except GreetingsLoadError as gle:
            QuestionLoader._logger.error(f'Load greeting questions error: {gle}')
        except Exception as e:
            QuestionLoader._logger.error(f'Unexpected error: {e}')
        finally:
            return result

    @staticmethod
    def _load_questions_from_file() -> List[GreetingQuestionDto]:
        """Main load questions method"""
        questions_dict = QuestionLoader._load_from_file(GreetingDefaultSettings.GREETING_QUESTIONS_FILE)
        questions = questions_dict.get('questions', [])

        if not isinstance(questions, list):  # non-list
            raise GreetingsLoadError(f'Questions are not as list! Content: {questions}')

        result = []
        for question in questions:
            # Check question structure
            if not QuestionLoader._validate(question):
                QuestionLoader._logger.error(f'Malformed question found, skipping it. Question: {question}')
                continue
            buttons = []
            replies = {}
            timeout = question.get(  # TODO: Int type check for global or move it to config
                'question_timeout',
                questions_dict.get('global_question_timeout', GreetingDefaultSettings.DEFAULT_QUESTION_TIMEOUT)
            )
            for i, opt in enumerate(question.get('options', [])):
                buttons.append(
                    InlineKeyboardButton(
                        text=opt.get('option_text', GreetingDefaultSettings.DEFAULT_QUESTION_OPTION),
                        callback_data=str(i),
                    ))
                replies[str(i)] = opt.get('reply_text', GreetingDefaultSettings.DEFAULT_QUESTION_REPLY)

            result.append(
                GreetingQuestionDto(
                    text=question.get('text', GreetingDefaultSettings.DEFAULT_QUESTION_TEXT),
                    keyboard=InlineKeyboardMarkup().row(*buttons),
                    timeout=timeout,
                    reply=replies,
                ))

        # Final questions check
        if not result:
            raise GreetingsLoadError(
                f'No valid questions were extracted from yaml file! Content: {questions_dict}'
            )
        return result

    @staticmethod
    def _validate(question) -> bool:
        """Super simple validator (no asserts)"""
        if not isinstance(question, dict):
            return False
        result = True
        result = result and question.get('name', False)
        result = result and question.get('text', False)
        result = result and isinstance(question.get('question_timeout', 0), int)  # Optional field, only type check

        options = question.get('options') if isinstance(question.get('options'), list) else []
        result = result and bool(options)
        result = result and len(options) > 0

        for opt in options:
            if not isinstance(opt, dict):
                result = False
                continue
            result = result and opt.get('option_text', False)
            result = result and opt.get('reply_text', False)
        return result

    @staticmethod
    def _load_from_file(file_path: Path) -> Dict:
        """Load dict from yaml file"""
        if not file_path.exists():
            raise GreetingsLoadError(
                f'Can not found yaml file with greeting questions by location: {file_path.absolute()}'
            )
        with file_path.open("r", encoding="utf8") as f:
            try:
                result = yaml.load(f)
            except ScannerError as se:
                raise GreetingsLoadError(f'Malformed questions file: {se}')
        if not isinstance(result, dict):
            raise GreetingsLoadError(f'Malformed (not a dict) questions file: {result}')
        return result

    @staticmethod
    def _set_default_greeting() -> List[GreetingQuestionDto]:
        """Default greeting that will be used if file not available/broken"""
        result = GreetingQuestionDto(
            text=GreetingDefaultSettings.DEFAULT_QUESTION_TEXT,
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(
                    text=GreetingDefaultSettings.DEFAULT_QUESTION_OPTION,
                    callback_data='1',
                ),
            ),
            timeout=GreetingDefaultSettings.DEFAULT_QUESTION_TIMEOUT,
            reply={'1': GreetingDefaultSettings.DEFAULT_QUESTION_REPLY},
        )
        return [result, ]


class QuestionProvider:
    _questions: List[GreetingQuestionDto] = QuestionLoader.load_questions()

    @staticmethod
    def get_question() -> GreetingQuestionDto:
        """
        This method return random question from greeting questions list
        :return: GreetingQuestionDto
        """
        return random.choice(QuestionProvider._questions)

    @staticmethod
    def reload_questions_list():
        """Reload greeting questions list"""
        QuestionProvider._questions = QuestionLoader.load_questions()
