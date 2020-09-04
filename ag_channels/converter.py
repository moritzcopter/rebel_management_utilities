import json


def converter(from_data_type, to_data_type, data):
    """
        Converter between different types of Dutch geodata. Takes a piece of
        geodata of a specified type, and converts it to another type.
        The function doesn't check validity of calls - i.e. you could try to
        convert the municipality "Amsterdam" to a single postcode, which would
        give non-sensical output.

        Params:
        - from_data_type (string) : the geodata type of the input data. Allowed
                                    values: "postcode", "municipality", "town",
                                    "province", "region".
        - to_data_type (string) : the geodata type of the output data. Allows
                                  the same values as 'from_data_type'.
        - data (string) : the to-be-converted geodata.

        Returns:
        - (string) : the converted geodata.

        Example:
        - To get the municipality corresponding to the postcode 1098AB, you
          would call: "convert("postcode", "municipality", "1098AB")".

        TODO:
        - filter non-sensical combinations of data types (e.g. converting from
          municipality to postcode).
        - right now, a call like: 'converter("postcode", "municipality", "12340")'
          would yield 'Oegstgeest', as the postcode 2340 lies in 'Oegstgeest', and
          our function checks if the postcode in the database is contained within
          the input postcode. We should change this to check if the input
          data is equal to the data in the database. Before we can change this, however,
          we should parse postcodes, and remove all but the four digits.
    """
    with open('geodata.json') as f:
        geodata = json.load(f)

        data_types_index = {
            'postcode': 0,
            'municipality': 1,
            'town': 2,
            'province': 3,
            'region': 4
        }

        try:
            for row in geodata:
                if row[data_types_index[from_data_type]] in data:
                    return row[data_types_index[to_data_type]]
        except KeyError:
            raise ValueError(f'from_data_type and to_data_type must have '
                             f'one of the following values: {", ".join(data_types_index.keys())}')
