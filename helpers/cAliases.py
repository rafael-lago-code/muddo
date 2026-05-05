class cAliases:
  _aliases = {}

  @classmethod
  def set(cls, aliases: dict):
    cls._aliases = aliases

  @classmethod
  def get(cls) -> dict:
    return cls._aliases
