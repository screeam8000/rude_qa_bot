import logging
import random
from typing import Dict, Any

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


class QuestionProvider:
    @staticmethod
    def get_question() -> GreetingQuestionDto:
        return QuestionProvider.__get_random_question()

    @staticmethod
    def __get_random_question():
        """
        This method create greeting question list of some questions
        then return first random question from list
        Note: if need more questions - need to rework this method
        :return: GreetingQuestionDto
        """
        greeting_question_ui = GreetingQuestionDto(
            text='{mention}, UI это API?',
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text='Да, определённо!', callback_data='да'),
                InlineKeyboardButton(text='Нет, обоссыте меня', callback_data='нет'),
            ),
            timeout=120,
            reply={
                'да': '*{first_name} считает, что да.*',
                'нет': '*{first_name} считает, что нет. ¯\\_(ツ)_/¯*',
            }
        )

        greeting_question_git = GreetingQuestionDto(
            text='{mention}, Git: merge или rebase?',
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text='Конечно merge', callback_data='merge'),
                InlineKeyboardButton(text='Конечно rebase', callback_data='rebase'),
            ),
            timeout=120,
            reply={
                'merge': '*{first_name} считает, что merge правильнее.*',
                'rebase': '*{first_name} считает, что rebase правильнее.*',
            }
        )

        greeting_question_bdd = GreetingQuestionDto(
            text='{mention}, BDD это круто?',
            keyboard=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text='Да, это круто!', callback_data='да'),
                InlineKeyboardButton(text='Нет, это хуйня!', callback_data='нет'),
            ),
            timeout=120,
            reply={
                'да': '*{first_name} считает, что да. ¯\\_(ツ)_/¯*',
                'нет': '*{first_name} считает, что нет.*',
            }
        )

        greeting_list = [greeting_question_ui, greeting_question_git, greeting_question_bdd]

        return random.choice(greeting_list)
