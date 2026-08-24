# P2 take comparison — inverse solve vs iPhone ARKit (calibrated)

Take `20260814_DefaultSlate_2`, 1472 frames @ 59.94 fps. Alignment lag 0f (0.000s), JawOpen corr 0.958.

**Reference is L/R-swapped**: the Blip mono video is mirrored (selfie convention), so the MHA solve is a mirror image of the ARKit stream. Mean Pearson vs mirrored ref **0.576** vs as-recorded ref 0.526.

Mean solve residual 0.45193; 51 active curves.

| curve | pearson | rmse | solved p95 | iphone p95 |
|---|---|---|---|---|
| EyeLookOutRight | 0.9901 | 0.036 | 0.8521 | 0.8854 |
| EyeLookInLeft | 0.9869 | 0.0442 | 0.8829 | 0.9617 |
| EyeLookOutLeft | 0.9864 | 0.0521 | 0.9897 | 1.0 |
| BrowDownRight | 0.9609 | 0.1497 | 1.0 | 0.7881 |
| JawOpen | 0.9581 | 0.0919 | 1.0 | 0.9613 |
| EyeLookInRight | 0.9464 | 0.0974 | 0.9937 | 1.0 |
| BrowDownLeft | 0.9394 | 0.1695 | 1.0 | 0.7883 |
| BrowOuterUpLeft | 0.9319 | 0.1563 | 0.9505 | 0.7176 |
| BrowOuterUpRight | 0.9195 | 0.1518 | 0.9252 | 0.7171 |
| MouthSmileLeft | 0.9086 | 0.1572 | 0.6342 | 0.8961 |
| MouthPucker | 0.885 | 0.0785 | 0.2603 | 0.1881 |
| EyeBlinkRight | 0.8681 | 0.1279 | 0.6848 | 0.8928 |
| CheekSquintLeft | 0.8553 | 0.2715 | 0.9123 | 0.2961 |
| EyeLookDownLeft | 0.8296 | 0.1264 | 0.4447 | 0.2186 |
| EyeLookDownRight | 0.8291 | 0.1283 | 0.4517 | 0.2185 |
| MouthSmileRight | 0.8164 | 0.2031 | 0.656 | 0.8861 |
| EyeLookUpRight | 0.7957 | 0.1323 | 0.5083 | 0.503 |
| EyeLookUpLeft | 0.7911 | 0.1342 | 0.512 | 0.5041 |
| EyeBlinkLeft | 0.7657 | 0.1623 | 0.7009 | 0.8927 |
| MouthLowerDownRight | 0.7592 | 0.2307 | 0.6073 | 0.8911 |
| NoseSneerLeft | 0.7574 | 0.1376 | 0.5167 | 0.728 |
| NoseSneerRight | 0.7443 | 0.1461 | 0.5703 | 0.695 |
| MouthRollLower | 0.7418 | 0.0602 | 0.1396 | 0.0163 |
| MouthLowerDownLeft | 0.7346 | 0.2339 | 0.6286 | 0.8925 |
| EyeWideRight | 0.7181 | 0.2311 | 0.7855 | 0.8739 |
| EyeSquintLeft | 0.6865 | 0.2145 | 0.5784 | 0.9041 |
| CheekSquintRight | 0.6673 | 0.237 | 0.7836 | 0.2799 |
| EyeWideLeft | 0.653 | 0.2699 | 0.7147 | 0.8738 |
| MouthUpperUpLeft | 0.6443 | 0.1294 | 0.3576 | 0.4151 |
| MouthShrugUpper | 0.6143 | 0.0953 | 0.2773 | 0.3035 |
| MouthUpperUpRight | 0.5998 | 0.118 | 0.334 | 0.3982 |
| EyeSquintRight | 0.5819 | 0.2356 | 0.4803 | 0.9043 |
| MouthFrownRight | 0.5682 | 0.1677 | 0.4347 | 0.1663 |
| MouthFrownLeft | 0.5664 | 0.1751 | 0.4607 | 0.1928 |
| CheekPuff | 0.4968 | 0.0201 | 0.0347 | 0.0018 |
| MouthStretchLeft | 0.4725 | 0.2265 | 0.6098 | 0.486 |
| MouthShrugLower | 0.4718 | 0.0402 | 0.0895 | 0.0 |
| MouthStretchRight | 0.4558 | 0.2351 | 0.614 | 0.4645 |
| MouthFunnel | 0.2354 | 0.1333 | 0.3352 | 0.2051 |
| MouthDimpleLeft | 0.211 | 0.1308 | 0.3215 | 0.0946 |
| MouthDimpleRight | 0.1576 | 0.131 | 0.3132 | 0.1133 |
| MouthPressRight | 0.1377 | 0.0529 | 0.0697 | 0.0 |
| JawRight | 0.0861 | 0.0422 | 0.0967 | 0.0 |
| MouthPressLeft | 0.0445 | 0.0491 | 0.0312 | 0.0 |
| JawForward | 0.0335 | 0.0866 | 0.0642 | 0.1779 |
| MouthRollUpper | 0.0299 | 0.1129 | 0.2114 | 0.1623 |
| JawLeft | 0.0 | 0.0349 | 0.0762 | 0.0274 |
| TongueOut | -0.0432 | 0.0854 | 0.1542 | 0.0009 |
| MouthLeft | -0.0991 | 0.0911 | 0.0829 | 0.0876 |
| MouthRight | -0.1401 | 0.064 | 0.049 | 0.075 |
| BrowInnerUp | -0.1965 | 0.3494 | 0.089 | 0.8074 |

Inactive in both streams (nothing to compare): none

iPhone curves the solver can't emit yet: MouthClose, HeadYaw, HeadPitch, HeadRoll, LeftEyeYaw, LeftEyePitch, LeftEyeRoll, RightEyeYaw, RightEyePitch, RightEyeRoll
(MouthClose comes from the ABP formula inversion in the definition fit; head/eye rotations are bone channels, not part of the 51-shape basis.)
