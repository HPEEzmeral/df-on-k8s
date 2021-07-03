class Yamlize(object):
    """
    Takes a string blob and formats it so it fits the model for a value in a ConfigMap with the expected indentation.

    Example, a string that looks like this:

    TestLine1
    TestLine2
      Now 3
    And 4

    Will be configured to:

    | (put after the key in the key/value area of the configmap
        TestLine1
        TestLine2
          Now 3
        And 4
    return the new string
    """
    @staticmethod
    def genConfigMapValue(content):
        INDENT = "    "
        result = "|\n"
        for line in content.splitlines():
            result += INDENT + line + "\n"
        return result
