
class GBConstants:
    """
    The constants used in the GreedyBoy bot.
    """
    # Constants
    DATE_FORMAT = '%d-%m-%Y' # '%Y-%m-%d'
    """
    The date format used in the files.
    """
    DATE_TIME_FORMAT = '%d-%m-%Y %H:%M:%S' # '%m-%d-%Y %H:%M:%S'
    """
    The date and time format used in the files.
    """
    PRINT_DATE_FORMAT = '%m/%d/%Y'
    """
    The date format used in the printed dates.
    """
    PRINT_DATE_TIME_FORMAT = '%m/%d/%Y %H:%M:%S'
    """
    The date and time format used in the printed dates.
    """
    FIAT_BALANCE_CHECK = 50.0
    """
    The minimum fiat balance allowed for the bot to use. Value is 50.0.
    """
    FIAT_CURRENCY = 'USD'
    """
    The fiat currency used in the bot.
    """
    MAX_TOKEN_ORDER = 500.0
    """
    The maximum token order allowed for the bot to use. Value is 500.0.
    """
    # Static Methods
    @staticmethod
    def getEMAValues() -> list[int]:
        """
        Returns the EMA values used in the bot.
        :return: The EMA values used in the bot.
        """
        return [5, 10, 20, 40, 50, 100, 200]
    @staticmethod
    def getCurrencyInitials() -> list[str]:
        """
        Returns the initials of the currencies.
        :return: The initials of the currencies.
        """
        return ['BTC', 'ETH', 'XRP', 'LTC', 'XDG', 'UNI', 'LINK', 'ADA', 'DOT', 'BCH']
    @staticmethod
    def getCurrencyNames() -> list[str]:
        """
        Returns the names of the currencies.
        :return: The names of the currencies.
        """
        return ['Bitcoin', 'Ethereum', 'Ripple', 'Litecoin', 'Dogecoin', 'Uniswap', 'Chainlink', 'Cardano', 'Polkadot', 'Bitcoin Cash']
    @staticmethod
    def getCurrencySymbols() -> list[str]:
        """
        Returns the symbols of the currencies.
        :return: The symbols of the currencies.
        """
        return ['₿', 'Ξ', 'X', 'Ł', 'Ð', 'U', 'L', '₳', '•', 'BCH']
    @staticmethod
    def getCurrencyDecimals() -> list[int]:
        """
        Returns the number of decimals of the currencies.
        :return: The number of decimals of the currencies.
        """
        return [8, 8, 6, 8, 2, 8, 8, 6, 8, 8]
    
    