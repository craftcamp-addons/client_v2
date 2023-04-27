from enum import Enum

from pydantic import BaseModel


class InitMessageModel(BaseModel):
    id: int


class HeartbeatMessageModel(InitMessageModel):
    pass


class TaskStatus(Enum):
    ERROR = 0
    CREATED = 1
    COMPLETED = 2
    SECONDCHECK = 3


class TaskModel(BaseModel):
    number: str
    status: TaskStatus


class TaskMessageModel(BaseModel):
    task_id: str
    model: TaskModel
