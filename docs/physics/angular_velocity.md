# Angular Velocity Vector (\(\vec{\omega}\))

The angular velocity vector describes how quickly and about which axis an object rotates. It has a magnitude (angular speed) and a direction following the right-hand rule.

## Magnitude – Angular Speed

- **Definition:** \(\omega = \frac{d\theta}{dt}\), where \(\theta\) is the rotation angle.
- **Units:** Radians per second (rad/s) are standard, though revolutions per minute (RPM) or degrees per second are also used.

## Direction – Axis of Rotation

- **Right-Hand Rule:** Curl the fingers of your right hand along the rotation direction; your thumb points along \(\vec{\omega}\).
- Because it depends on a convention, \(\vec{\omega}\) is an axial (pseudo) vector.

## Relationship to Linear Velocity

For any point on the rotating body with position vector \(\vec{r}\) from a point on the rotation axis, the linear velocity \(\vec{v}\) is given by the cross product

\[
\vec{v} = \vec{\omega} \times \vec{r}.
\]

This shows that \(\vec{v}\) is perpendicular to both \(\vec{\omega}\) and \(\vec{r}\), aligning with the tangential direction of circular motion.

## Component Form

In Cartesian coordinates the vector can be decomposed as

\[
\vec{\omega} = \omega_x \hat{\imath} + \omega_y \hat{\jmath} + \omega_z \hat{k},
\]

enabling analysis of complex 3D rotational motion.

## Applications

- **Rigid Body Dynamics:** Forms the basis for calculating angular momentum, torque, and rotational kinetic energy.
- **Aerospace Engineering:** Describes and controls satellite and aircraft attitude.
- **Robotics:** Governs manipulator joint motion and end-effector orientation.
- **Fluid Dynamics:** Extends to vorticity, describing local fluid element rotation.

Understanding \(\vec{\omega}\) is therefore essential across physics and engineering disciplines.
