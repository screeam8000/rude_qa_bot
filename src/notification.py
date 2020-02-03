from copy import copy
from random import shuffle
from typing import Dict, List

from const import NotificationTemplateList, Command
from dto import CommandDto


class Notification:
    _notification: Dict[str, List[str]]

    def __init__(self):
        self._notification = dict()

    def _init_list(self, list_name: str, source_list: list):
        self._notification[list_name] = copy(source_list)
        shuffle(self._notification[list_name])

    def _get_restrict_notification_text(self, first_name: str, duration_text: str, command: CommandDto,
                                        notification_list: List) -> str:
        template_text = self._get_notification(command.text, notification_list)
        return template_text.format(
            first_name=first_name,
            duration_text=duration_text,
        )

    def _get_simple_notification_text(self, first_name: str, command: str, notification_list: List) -> str:
        template_text = self._get_notification(command, notification_list)
        return template_text.format(
            first_name=first_name
        )

    def _get_notification(self, command_name: str, source_list: list) -> str:
        self._notification.setdefault(command_name, list())
        if len(self._notification[command_name]) == 0:
            self._init_list(command_name, source_list)
        return self._notification[command_name].pop()

    def read_only(self, first_name: str, duration_text: str) -> str:
        return self._get_restrict_notification_text(first_name=first_name, duration_text=duration_text,
                                                    command=Command.RO,
                                                    notification_list=NotificationTemplateList.READ_ONLY)

    def text_only(self, first_name: str, duration_text: str) -> str:
        return self._get_restrict_notification_text(first_name=first_name, duration_text=duration_text,
                                                    command=Command.TO,
                                                    notification_list=NotificationTemplateList.TEXT_ONLY)

    def read_write(self, first_name: str) -> str:
        return self._get_simple_notification_text(first_name=first_name, command=Command.RW,
                                                  notification_list=NotificationTemplateList.READ_WRITE)

    def timeout_kick(self, first_name: str) -> str:
        return self._get_simple_notification_text(first_name=first_name, command=Command.TK,
                                                  notification_list=NotificationTemplateList.TIMEOUT_KICK)

    def ban_kick(self, first_name: str, duration_text: str) -> str:
        return self._get_restrict_notification_text(first_name=first_name, duration_text=duration_text,
                                                    command=Command.BAN,
                                                    notification_list=NotificationTemplateList.BAN_KICK)

    def unauthorized_punishment(self, first_name: str) -> str:
        return self._get_simple_notification_text(first_name=first_name, command=Command.SR,
                                                  notification_list=NotificationTemplateList.UNAUTHORIZED_PUNISHMENT)
