import matplotlib.pyplot as plt
import math

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, dt):
        """
        Initializes the PID controller.
        
        Args:
            Kp: Proportional gain.
            Ki: Integral gain.
            Kd: Derivative gain.
            setpoint: Desired target value.
            dt: Time step (sampling time).
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.dt = dt

        self.previous_error = 0
        self.integral = 0

    def compute(self, measured_value):
        """
        Compute the control signal based on the measured value.
        
        Args:
            measured_value: The current value from the system.
        
        Returns:
            control_signal: The output control signal.
        """
        # Calculate error
        error = self.setpoint - measured_value

        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += error * self.dt
        I = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.previous_error) / self.dt
        D = self.Kd * derivative

        # Compute control signal
        control_signal = P + I + D

        # Update previous error
        self.previous_error = error

        return control_signal

# Example usage
if __name__ == "__main__":
    # Initialize PID controller with gains and setpoint
    pid = PIDController(Kp=1, Ki=0.8, Kd=0.5, setpoint=0, dt=0.1)

    # Simulate a system
    measured_value = 0  # Initial measured value
    measured_values = []
    control_signals = []
    time_steps = []

    for i in range(100):
        pid.setpoint = math.cos(i/10)
        control_signal = pid.compute(measured_value)
        measured_values.append(measured_value)
        control_signals.append(control_signal)
        time_steps.append(i * pid.dt)

        # Update measured value (simulating system response)
        measured_value += control_signal * 0.1  # Assume system gain of 0.1

    # Plot results
    plt.figure(figsize=(10, 5))

    # Plot measured value
    plt.plot(time_steps, measured_values, label="Measured Value")

    # Plot control signal
    plt.plot(time_steps, control_signals, label="Control Signal")

    # Add labels and legend
    plt.title("PID Controller Simulation")
    plt.xlabel("Time (s)")
    plt.ylabel("Value")
    plt.legend()
    plt.grid()

    # Show plot
    plt.savefig("PID.png")
