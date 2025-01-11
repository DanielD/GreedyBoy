import pandas as pd
from GBConstants import GBConstants

class GBUtilities:
    """
    A class that contains utility functions for GreedyBoy.
    """
    @staticmethod
    def getMaxFiatBalance(fiatBalance: float, testTime: float = None) -> float:
        """
        Returns the maximum fiat balance allowed for the bot to use.
        :param fiatBalance: The current fiat balance.
        :param testTime: The time of the test. If None, the function will return the current fiat balance.
        :return: The maximum fiat balance allowed.
        """
        if testTime is not None:
            return fiatBalance / 2.0 if fiatBalance / 2.0 < GBConstants.FIAT_BALANCE_CHECK else GBConstants.FIAT_BALANCE_CHECK
        else:
            return fiatBalance
    @staticmethod
    def ensureCorrectFormat(value: any, throwIfMultiRow: bool = False, variableName: str = 'value') -> any:
        """
        Ensures that the given value is in the correct format for concatenation.
        :param value: The value to ensure the format of, which can be a dict, Series, or DataFrame.
        :param throwIfMultiRow: Whether to throw an error if the value has more than one row.
        :param variableName: The name of the variable.
        :return: The value in the correct format.
        :raises ValueError: If the value is not in the correct format.
        :raises ValueError: If the value has more than one row and `throwIfMultiRow` is True.
        """
        # Ensure `value` is in the correct format for concatenation
        if isinstance(value, pd.DataFrame):
            # If it's already a DataFrame, use the first row
            if throwIfMultiRow and value.shape[0] > 1:
                raise ValueError("`{0}` must have only one row.".format(variableName))
            new_row = value.iloc[0].to_dict()
        elif isinstance(value, pd.Series):
            # If it's a Series, convert it to a dictionary
            new_row = value.to_dict()
        elif isinstance(value, dict):
            # If it's a dictionary, use it directly
            new_row = value
        else:
            raise ValueError("`{0}` must be a dict, Series, or DataFrame.".format(variableName))
        return new_row
    @staticmethod
    def createNewDataFrameRow(value: any, throwIfMultiRow: bool = False, variableName: str = 'value') -> pd.DataFrame:
        """
        Creates a new DataFrame row from the given value.
        :param value: The value to ensure the format of, which can be a dict, Series, or DataFrame.
        :param throwIfMultiRow: Whether to throw an error if the value has more than one row.
        :param variableName: The name of the variable.
        :return: The new DataFrame row.
        :raises ValueError: If the value is not in the correct format.
        :raises ValueError: If the value has more than one row and `throwIfMultiRow` is True.
        """
        new_row = GBUtilities.ensureCorrectFormat(value, throwIfMultiRow, variableName)
        # Create a new DataFrame row
        new_row_df = pd.DataFrame([new_row])

        # Exclude empty or all-NA columns before concatenation
        new_row_df = new_row_df.dropna(how='all', axis=1)
        return new_row_df