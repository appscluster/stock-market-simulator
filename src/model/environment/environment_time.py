"""Time implementations for the trading environment."""


class EnvironmentTime(object):
  """Base class for time in trading environments."""

  def GetCurrentTime(self):
    """Returns the current time."""
    raise NotImplementedError('Override this method in a subclass.')

  def Step(self, units):
    """Steps the time forward by given number of time units.

    Args:
      units: Number of time units to step forward.
    """
    raise NotImplementedError('Override this method in a subclass.')


class IntegerTime(EnvironmentTime):
  """Simple time implementation for trading environments."""

  def __init__(self, start_time=0, time_unit=1):
    """Initialize the integer time.

    Args:
      start_time: Initial time for this object.
      time_unit: Length of one time step.
    """
    self.time = start_time
    self.time_unit = time_unit

  def GetCurrentTime(self):
    """Gets the current time.

    Returns:
      Integer value for current time.
    """
    return self.time

  def Step(self, steps=1):
    """Step time forward by given number of time units.

    The length of one step (time unit) is defined in initialization.

    Args:
      steps: Number of time units to move forward in time.
    """
    self.time += self.time_unit * steps
