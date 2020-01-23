import logging
import random
import yaml

from pathlib import Path
from typing import Dict, Any, List

from telebot.types import InlineKeyboardButton, User, InlineKeyboardMarkup, Message

from dto import GreetingQuestionDto, NewbieDto
from error import UserAlreadyInStorageError, UserNotFoundInStorageError, UserStorageUpdateError


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
    GREETING_QUESTIONS_FILE: Path = Path('./resources/questions.yaml')
    DEFAULT_QUESTION_TEXT = '{mention} You ok?'
    DEFAULT_QUESTION_OPTION = 'Yep'
    DEFAULT_QUESTION_REPLY = 'Roger!'
    DEFAULT_QUESTION_TIMEOUT = 120

    @staticmethod
    def load_questions() -> List[GreetingQuestionDto]:
        """
        This method loads greeting questions list from yaml file
        Note: dynamical reload can be added here
        :return: List[GreetingQuestionDto] - list with greeting question dto's
        """
        result = []
        if QuestionLoader.GREETING_QUESTIONS_FILE.exists():
            with QuestionLoader.GREETING_QUESTIONS_FILE.open("r", encoding="utf8") as f:
                questions_dict = yaml.load(f)
            for question in questions_dict.get('questions', []):
                # TODO: validate question structure  # QuestionLoader.validate(question)
                buttons = []
                replies = {}
                timeout = question.get(
                    'question_timeout',
                    questions_dict.get('global_question_timeout', QuestionLoader.DEFAULT_QUESTION_TIMEOUT)
                )
                for i, opt in enumerate(question.get('options', [])):
                    buttons.append(
                        InlineKeyboardButton(
                            text=opt.get('option_text', QuestionLoader.DEFAULT_QUESTION_OPTION),
                            callback_data=str(i),
                        ))
                    replies[str(i)] = opt.get('reply_text', QuestionLoader.DEFAULT_QUESTION_REPLY)

                result.append(
                    GreetingQuestionDto(
                        text=question.get('text', QuestionLoader.DEFAULT_QUESTION_TEXT),
                        keyboard=InlineKeyboardMarkup().row(*buttons),
                        timeout=timeout,
                        reply=replies,
                    ))

        return result


class QuestionProvider:
    _questions: List[GreetingQuestionDto] = QuestionLoader.load_questions()

    @staticmethod
    def get_question() -> GreetingQuestionDto:
        """
        This method return random question from greeting questions list
        :return: GreetingQuestionDto
        """
        return random.choice(QuestionProvider._questions)
