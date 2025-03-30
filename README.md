# INF2009_T2


## At Home ELISS Push-up Machine
This project showcases an at-home simulation of Singapore's IPPT ELISS Machine, with the goal of allowing NSFs and NSmen to remotely experience the push-up station, and additionally receive feedback on push-up posture.

![At Home ELISS Push-up Machine User Flow Diagram](INF2009_AHEPM_Userflow.png)

## Problem Statement
In many military camps, the ELISS (Electronic IPPT Scoring System) machine is used to measure the quality and count of a person’s push-ups. However, users frequently feedback about the inaccuracy of the machine’s assessments, which may be attributable to the subtle variations in push-up form. These inaccuracies can often lead to frustration and unreliable performance metrics. Given the importance of proper push-up form, there is a need for an at-home solution for NSFs and NSmen to train and get acquainted with how the machine works, providing them with accurate and real-time feedback

## Devices / Components
1. Raspberry Pi 3 Model B+
2. Raspberry Pi 5
3. GrovePi+
4. Webcam
5. Cytron - Ultrasonic Ranging Module SR04P
6. Grove - LCD RGB Backlight
7. Grove - Buzzer
8. Grove - Red LED
9. Grove - Green LED
10. Speaker
10. Firebase Database
11. Flask Webpage

## Methodology / Project Timeline / Hardware Justification
The initial idea of the project was thought up in Weeks 2-3 of this trimester.
After consulting, the project was green-lit and we began preparations.

Weeks 4-7 were spent coming up with ideas and sourcing the hardware needed for the project.
We decided to use the *GrovePi+* as it had compatible sensors that were core modules in our push-up system.
Additionally, some of our group members had previously worked with the *GrovePi+*.
We ran basic tests on the hardware and finalised our ideas, resulting in the *At Home ELISS Push-up Machine*, utilising the various sensors aforementioned.

Initial tests with the *GrovePi+* and the pose estimation implementation resulted in poor compatibility issues.
The *GrovePi+* was a discontinued product, with it no longer having official support.
As such, the *GrovePi+* firmware needed to be ran on an older, legacy OS.
On the other hand, the use of *mediapipe* needed the latest versions of *Python*, and the firmware of the legacy OS did not allow the *opencv + mediapipe* pose estimation to perform well.
Therefore, we decided to use two *Raspberry Pis* in order to faciliate our requirements.

With the use of *Message Queuing Telemetry Transport (MQTT)*, we are able to allow the two *Pis* to communicate and have each *Pi* be responsible for their own responsibilities.
The older *Raspberry Pi 3 Model B+* has been imaged with the legacy Bullseye OS, and has the *GrovePi+* connected to it, allowing the various Grove sensors to function properly.
Contrarily, the *Raspberry Pi 5*, with a webcam connected to it, as well as its improved hardware, allowed for the *opencv + mediapipe* pose estimation to have a higher performance.
Now, the basic system architecture is met, and we are able to work on the program itself.

![At Home ELISS Push-up Machine Block Diagram](INF2009_BlockDiagram1.png)

Bulk of the time spent on the project was working out how the components functioned and synced with each other, in order to provide the user with an accurate and comfortable solution to practice their push-up form on.

On the *Pi* side of things, utilising *MQTT* in order for both *Pis* to communicate was a key component in order to allow a smooth experience.
The use of *MQTT* allowed for the *Camera Pi* to notify the *Grove Pi* on which output sensors needed to run their various functionalities to provide feedback to the user.
Likewise, the *Grove Pi* could also then notify the *Camera Pi* on when to pinpoint bad posture through the use of ultrasonic ranger readings.

The pose estimation module utilised *opencv* and *mediapipe's* pose module in order to detect users on the camera feedback, placing landmarks on the user which were then used to estimate their posture.
We used these landmarks to calculate the angles of the user's elbow, shoulder and hip, which were then used to determine a good or bad push-up posture.

With the *Grove sensors*, the *Ultrasonic Ranger* was implemented as a secondary input to the pose estimation module, with the use of measuring the distance between the ranger and the user's chest.
This distance measurement supplemented the detection of bad postures, by detecting abnormal movement that signaled a push-up that was not done in a flowing motion.

Furthermore, we used *Firebase* in order to store the data obtained from the user's push-up session, including the push-up count and the pose estimation data captured.

On the dashboard side of things, we used *Flask* to create a basic web page in order to display the push-up and pose estimation data, which are feedback for the user's posture, providing them with insights on their push-up form and what bad postures are affecting their push-up accuracy.

### Issues faced / Improved Methodology
Throughout the project's progress, we were faced with multiple issues.

One hardware issue we faced, was that after substantial amount of use of the *Grove* sensors, we found that our *Grove - Ultrasonic Ranger* was faulty and had issues when the process was running on high load. This led to a replacement in the component to be the *Cytron - Ultrasonic Ranging Module SR04P* instead.

The main issue we had a hard time figuring out was how the push-up logic worked in order for both *Pis* to sync up and provide the user with an accurate and comfortable experience. Initially, when using just the data from the pose estimation, we determined the user to be two states, namely, 'Good Posture' and 'Bad Posture'. The angles determined from the pose estimation landmarks were calibrated to determine the user's state. 

For example, when the user is in a proper push-up form, they are expected to have their arms and back straight, and with our landmarks, the elbow and hip angle would have to be calibrated towards an angle of a straight line. Likewise, when the user is moving to the bottom of their push-up, the elbow and shoulder angle would also have to be calibrated. However, this meant that when the user was not at an acceptable apex or bottom of their push-up, they would always be in a 'Bad Posture', which is not the intention of our project.

In order for our program to simulate the IPPT ELISS machine, this logic would have to be improved. We experimented with multiple methods, and with much time spent troubleshooting, we determined that the secondary data input of the *Ultrasonic Ranger* would supplement the posture estimation well. When the camera module detects that the user is doing a push-up, it categorizes the motion as 'up' and 'down', and the *Grove* module will use this state to determine the function of the *Ultrasonic Ranger*. 

The *Ultrasonic Ranger* would capture the distance between the user's chest and the ground, with the apex and bottom of the push-up as key baselines used to determine the user's push-up form. If the user were to not fully go down, not properly straighten their arms when returning to a rest position, or if their hips are sagging or up in the air, it would be considered as a bad posture. Now, the camera module will capture the screenshot at which this bad posture is detected, and when the pose estimation module determines what issues form this bad posture, the data will then be stored in *Firebase* to be used in the dashboard.

## Workload Allocation
The workload allocation was not simple, as there were only two physical *Pis*, with MQTT requiring a physical meet up in order to test and make progress on.
As such, we mainly worked on the project as we met up for lab sessions, with additional meetups when integrating multiple components.

| Name | Component |
| --- | --- |
| Samuel Song Yuhao | Project Management, Pose Estimation Functionality |
| Koh Zhe Huai Malcolm | Push-up Functionality, MQTT, Data Connectivity to Firebase | 
| Chung Eng Ee | Sensors/Grove Components, MQTT |
| Toh Cheng Kiat Brendan | Dashboard & Firebase Implementation |
| Low Yue Qian | Pose Estimation Integration with Camera OpenCV Functionality | 

## Website Dashboard Github Repo
Link: https://github.com/bren37/INF2009_T2
