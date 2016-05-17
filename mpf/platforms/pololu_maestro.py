"""Pololu Maestro servo controller platform"""

import logging
from mpf.core.platform import ServoPlatform
import serial


class HardwarePlatform(ServoPlatform):
    """Supports the Pololu Maestro servo controllers via PySerial. Works with
    Micro Maestro 6, and Mini Maestro 12, 18, and 24.
    """

    def __init__(self, machine):
        super().__init__(machine)
        self.log = logging.getLogger("Pololu Maestro")
        self.log.debug("Configuring template hardware interface.")
        self.config = self.machine.config['pololu_maestro']
        self.platform = None

        self.cmd_header = chr(0xaa) + chr(0xc)
        self.serial = None

    def __repr__(self):
        return '<Platform.Pololu_Maestro>'

    def initialize(self):
        """Method is called after all hardware platforms were instantiated.

        """
        super().initialize()

        # validate our config (has to be in intialize since config_processor
        # is not read in __init__)
        self.machine.config_validator.validate_config("pololu_maestro",
                                                      self.config)

        # load platform
        self.platform = self.machine.get_platform_sections("pololu_maestro",
                                                           None)

        self.serial = serial.Serial(self.platform.config['port'])

    def stop(self):
        self.serial.close()

    def servo_go_to_position(self, number, position):
        # Set channel to a specified target value.  Servo will begin moving
        # based on Speed and Acceleration parameters previously set.
        # Target values will be constrained within Min and Max range, if set.
        # For servos, target represents the pulse width in of
        # quarter-microseconds.
        # Servo center is at 1500 microseconds, or 6000 quarter-microseconds
        # Typcially valid servo range is 3000 to 9000 quarter-microseconds
        # If channel is configured for digital output, values < 6000 =
        # Low ouput

        # if Min is defined and Target is below, force to Min
        if (self.config['servo_min'] > 0 and
                position < self.config['servo_min']):
            position = self.config['servo_min']

        # if Max is defined and Target is above, force to Max
        if (self.config['servo_max'] > 0 and
                position > self.config['servo_max']):
            position = self.config['servo_max']
        #
        lsb = position & 0x7f  # 7 bits for least significant byte
        msb = (position >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        # Send Pololu intro, device number, command, channel, and target
        # lsb/msb
        cmd = self.cmd_header + chr(0x04) + chr(number) + chr(lsb) + chr(msb)
        self.serial.write(cmd)

    def set_speed(self, number, speed):
        """Set the speed of the channel.

        Speed is measured as 0.25microseconds/10milliseconds

        For the standard 1ms pulse width change to move a servo between
        extremes, a speed of 1 will take 1 minute, and a speed of 60 would take
        1 second.

        Speed of 0 is unrestricted.

        Args:
            number:
            speed:

        Returns:

        """
        lsb = speed & 0x7f  # 7 bits for least significant byte
        msb = (speed >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = self.cmd_header + chr(0x07) + chr(number) + chr(lsb) + chr(msb)
        self.serial.write(cmd)

    def set_acceleration(self, number, accel):
        """Set acceleration of channel.

        This provide soft starts and finishes when servo moves to target
        position.

        Valid values are from 0 to 255. 0=unrestricted, 1 is slowest start.
        A value of 1 will take the servo about 3s to move between 1ms to 2ms
        range.

        """
        lsb = accel & 0x7f  # 7 bits for least significant byte
        msb = (accel >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = self.cmd_header + chr(0x09) + chr(chan) + chr(lsb) + chr(msb)
        self.serial.write(cmd)