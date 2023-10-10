from abc import ABC, abstractmethod
from ..InternalTyping import WorkLoadData, AnalysisData
from typing import List


class DatasetInterface(ABC):
    @abstractmethod
    def convertToWorkloadFormat(
        self, load_real_multi_turn: bool = True     # FIXME: load_real_multi_turn means simluate human input time
    ) -> List[WorkLoadData]:
        pass

    @abstractmethod
    def convertToAnalysisFormat(self) -> List[AnalysisData]:
        pass

    @abstractmethod
    def getPrompts(self) -> List[str]:
        pass
