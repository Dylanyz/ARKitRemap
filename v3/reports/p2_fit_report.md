# P2 definition fit — RM_MHA_to_ARKit.json

52 outputs ({'weighted_sum': 47, 'passthrough': 4, 'iphone-calibrated': 1}), 55 feature nodes, 164 input curves. Fit R2 mean 0.9195, min 0.3678.
Null outputs: none

| output | kind | r2 | terms |
|---|---|---|---|
| EyeBlinkLeft | weighted_sum | 0.9738 | eyeBlinkL=0.8136, eyeParallelLookDirection=0.0421, eyeRelaxL=0.3125, eyelashesUpINL=0.3622, eyelashesUpOUTL=0.3639 |
| EyeLookDownLeft | weighted_sum | 0.9969 | eyeFaceScrunchL=0.0227, eyeLookDownL=0.9659, eyeLowerLidDownL=0.3779, eyeRelaxL=0.0582 |
| EyeLookInLeft | passthrough | 0.9984 | eyeLookRightL=1.0 |
| EyeLookOutLeft | passthrough | 0.9995 | eyeLookLeftL=1.0 |
| EyeLookUpLeft | weighted_sum | 0.9989 | eyeFaceScrunchL=0.056, eyeLookUpL=0.995, eyeLowerLidDownL=0.4019, eyeLowerLidUpL=0.0742 |
| EyeSquintLeft | weighted_sum | 0.922 | eyeLowerLidUpL=0.3495, eyeParallelLookDirection=0.1041, eyeSquintInnerL=0.7476, eyeUpperLidUpL=0.0546 |
| EyeWideLeft | weighted_sum | 0.9301 | eyeFaceScrunchL=1.4051, eyeLowerLidDownL=0.4276, eyeLowerLidUpL=0.0259, eyeParallelLookDirection=0.2013, sdk:eyeUpperLidUpL:EyeWideLeft=1.0, eyeWidenL=0.9982, eyelashesUpINL=0.9101, eyelashesUpOUTL=0.9144, mouthCheekSuckL=0.026 |
| EyeBlinkRight | weighted_sum | 0.9856 | eyeBlinkR=0.8583, eyeRelaxR=0.314, eyelashesUpINR=0.2574, sdk:eyelashesUpOUTR:EyeBlinkRight=1.0 |
| EyeLookDownRight | weighted_sum | 0.9973 | eyeFaceScrunchR=0.1182, eyeLookDownR=0.9637, eyeLowerLidDownR=0.3524, eyeRelaxR=0.0587 |
| EyeLookInRight | weighted_sum | 0.9994 | eyeLookLeftR=0.9958, eyeLowerLidUpR=0.0499 |
| EyeLookOutRight | weighted_sum | 0.9993 | eyeLookRightR=0.9993, eyeLowerLidUpR=0.0534 |
| EyeLookUpRight | weighted_sum | 0.999 | eyeFaceScrunchR=0.1455, eyeLookUpR=0.9941, eyeLowerLidDownR=0.3687, eyeLowerLidUpR=0.0652, eyelashesUpOUTR=0.0315 |
| EyeSquintRight | weighted_sum | 0.9464 | eyeLowerLidUpR=0.4039, eyeParallelLookDirection=0.0891, eyeSquintInnerR=0.8645, eyeUpperLidUpR=0.0615, noseNostrilDepressR=0.1035 |
| EyeWideRight | weighted_sum | 0.9542 | eyeFaceScrunchR=1.1587, eyeLowerLidDownR=0.3856, eyeParallelLookDirection=0.1533, sdk:eyeUpperLidUpR:EyeWideRight=1.0, eyeWidenR=1.0055, eyelashesUpINR=0.6385, sdk:eyelashesUpOUTR:EyeWideRight=1.0 |
| JawForward | weighted_sum | 0.9451 | jawFwd=0.9051, neckStretchL=0.1019, neckStretchR=0.1094, neckThroatDown=0.0297 |
| JawLeft | weighted_sum | 0.9347 | jawLeft=0.8928 |
| JawRight | weighted_sum | 0.9701 | jawBack=0.0442, jawChinCompressR=0.0379, jawRight=0.9521, mouthCheekBlowR=0.0487 |
| JawOpen | weighted_sum | 0.9989 | jawBack=0.0516, jawOpen=0.9646, neckDigastricDown=0.0371, neckStretchL=0.0563, neckStretchR=0.0519 |
| MouthFunnel | weighted_sum | 0.7336 | mouthCornerSharpenUL=0.1297, mouthCornerSharpenUR=0.2191, mouthFunnelDL=0.0999, mouthFunnelDR=0.3033, mouthFunnelUR=0.0944, mouthLowerLipRollOutR=0.0997 |
| MouthPucker | weighted_sum | 0.9734 | mouthCheekSuckL=0.0263, mouthCheekSuckR=0.0381, mouthLipsBlowL=0.0204, mouthLipsBlowR=0.0403, mouthLipsPressL=0.045, mouthLipsPressR=0.0379, mouthLipsPurseDL=0.2018, mouthLipsPurseDR=0.1844, mouthLipsPurseUL=0.1418, mouthLipsPurseUR=0.1722, mouthLipsStickyLPh2=0.0245, mouthLipsStickyRPh2=0.0267, mouthLipsStickyRPh3=0.0238, mouthLipsTowardsDL=0.1381, mouthLipsTowardsDR=0.1242, mouthLipsTowardsUL=0.1571, mouthLipsTowardsUR=0.1325, mouthLowerLipRollOutL=0.1226, mouthLowerLipRollOutR=0.0554, mouthPressUR=0.0262, mouthUpperLipRollOutL=0.1259, mouthUpperLipRollOutR=0.0799 |
| MouthLeft | passthrough | 0.9976 | mouthLeft=1.0 |
| MouthRight | passthrough | 0.9979 | mouthRight=1.0 |
| MouthSmileLeft | weighted_sum | 0.9881 | mouthCornerPullL=0.8234, mouthLipsBlowR=0.046, mouthSharpCornerPullL=0.534 |
| MouthSmileRight | weighted_sum | 0.986 | mouthCheekBlowL=0.0723, mouthCornerPullR=0.8147, mouthSharpCornerPullR=0.494 |
| MouthFrownLeft | weighted_sum | 0.9927 | mouthCornerDepressL=0.986, mouthCornerRounderDL=0.0318, mouthDown=0.1242, mouthLipsPressL=0.225, mouthLipsThinInwardDL=0.0208, mouthLipsThinInwardUL=0.0312, mouthLowerLipBiteL=0.0663, mouthPressDL=0.0367 |
| MouthFrownRight | weighted_sum | 0.9928 | mouthCornerDepressR=0.9511, mouthCornerRounderDR=0.0341, mouthDown=0.1037, mouthLipsPressR=0.2746, mouthLipsThinInwardDR=0.0227, mouthLipsThinInwardUR=0.0271, mouthLowerLipBiteR=0.0533, mouthPressDR=0.0324, mouthUpperLipRollOutR=0.0338 |
| MouthDimpleLeft | weighted_sum | 0.5933 | jawChinRaiseDL=0.0568, mouthCheekBlowR=0.1106, mouthDimpleL=0.3937, mouthLipsPressL=0.3283, mouthLipsPressR=0.138, mouthPressUL=0.0386, mouthSharpCornerPullL=0.1127 |
| MouthDimpleRight | weighted_sum | 0.5937 | mouthCheekBlowL=0.1014, mouthDimpleR=0.4152, mouthLipsPressL=0.0947, mouthLipsPressR=0.4876, mouthPressUR=0.0287, mouthSharpCornerPullR=0.0562, mouthUp=0.0397 |
| MouthStretchLeft | weighted_sum | 0.984 | jawChinCompressL=0.0354, jawChinCompressR=0.0229, mouthCheekBlowR=0.1032, mouthLipsPullUL=0.0441, mouthLipsThinDL=0.0353, mouthLowerLipRollOutL=0.0311, mouthLowerLipShiftLeft=0.1096, mouthStretchL=0.8891, neckDigastricUp=0.0222, neckStretchL=0.0316 |
| MouthStretchRight | weighted_sum | 0.9867 | jawChinCompressL=0.028, jawChinCompressR=0.0318, jawChinRaiseDL=0.0266, mouthCheekBlowL=0.1019, mouthLipsPullUR=0.0386, mouthLipsThinDR=0.032, mouthLowerLipRollOutR=0.0858, mouthLowerLipShiftRight=0.0423, mouthStretchR=0.8829, mouthUpperLipBiteL=0.0393, neckDigastricUp=0.0225, neckStretchR=0.0396 |
| MouthRollLower | weighted_sum | 0.9684 | mouthLowerLipBiteL=0.2688, mouthLowerLipBiteR=0.2642, mouthLowerLipRollInL=0.5145, mouthLowerLipRollInR=0.4343, mouthUpperLipRollInL=0.0553 |
| MouthRollUpper | weighted_sum | 0.7206 | mouthLipsPullUR=0.0821, mouthLipsTightenUL=0.0408, mouthLipsTightenUR=0.0318, mouthUp=0.0256, mouthUpperLipBiteL=0.1458, mouthUpperLipBiteR=0.2012, mouthUpperLipRollInL=0.3163, mouthUpperLipRollInR=0.387, mouthUpperLipTowardsTeethL=0.0369, mouthUpperLipTowardsTeethR=0.039, noseNasolabialDeepenL=0.0279, noseNostrilDepressR=0.0605 |
| MouthShrugLower | weighted_sum | 0.8391 | jawChinCompressL=0.1157, jawChinCompressR=0.1132, jawChinRaiseDL=0.4756, jawChinRaiseDR=0.4777, mouthCornerSharpenDR=0.0878, mouthLipsPurseUR=0.0329, mouthLipsStickyLPh1=0.0461, mouthLipsStickyLPh2=0.0433, mouthLipsStickyLPh3=0.0394, mouthLipsStickyRPh1=0.041, mouthLipsStickyRPh2=0.0348, mouthLipsStickyRPh3=0.0274, mouthLipsTightenDL=0.0355, mouthLipsTowardsUL=0.0546, mouthLipsTowardsUR=0.0591, mouthLowerLipBiteR=0.0249, mouthLowerLipTowardsTeethL=0.0708, mouthLowerLipTowardsTeethR=0.0703, mouthPressDL=0.0671, mouthPressDR=0.0635, mouthUp=0.156, neckDigastricDown=0.0207, neckDigastricUp=0.0814, neckThroatUp=0.0279 |
| MouthShrugUpper | weighted_sum | 0.7376 | jawChinRaiseUL=0.4849, jawChinRaiseUR=0.4892, mouthCheekSuckL=0.098, mouthCheekSuckR=0.1004, mouthFunnelUL=0.045, mouthLipsPullUL=0.1853, mouthLipsPullUR=0.3598, mouthLipsThinInwardUL=0.0473, mouthLipsThinInwardUR=0.0537, mouthLipsTightenUL=0.1892, mouthLipsTightenUR=0.1686, mouthPressUL=0.0429, mouthUp=0.168 |
| MouthPressLeft | weighted_sum | 0.972 | jawChinRaiseDL=0.0267, mouthLowerLipBiteL=0.5763, mouthLowerLipRollInL=0.0483, mouthLowerLipTowardsTeethL=0.0258, mouthPressDL=0.5734, mouthPressUL=0.3758, mouthUpperLipBiteL=0.2296 |
| MouthPressRight | weighted_sum | 0.9511 | mouthLipsTightenDR=0.0423, mouthLowerLipBiteR=0.5847, mouthLowerLipTowardsTeethR=0.025, mouthPressDR=0.5642, mouthPressUR=0.3874, mouthUpperLipBiteR=0.2687, mouthUpperLipRollInR=0.0797 |
| MouthLowerDownLeft | weighted_sum | 0.8974 | jawChinCompressR=0.0694, jawChinRaiseDR=0.1176, jawChinRaiseUL=0.02, mouthCheekBlowR=0.1021, mouthCornerSharpenDL=0.585, mouthCornerSharpenDR=0.3908, mouthDown=0.0993, mouthFunnelDL=0.17, mouthLipsBlowL=0.0484, mouthLipsPressL=0.0223, mouthLipsPushDR=0.0699, mouthLipsStickyLPh1=0.0268, mouthLipsStickyRPh1=0.0615, mouthLipsThinInwardDR=0.0362, mouthLowerLipDepressL=0.4749, mouthLowerLipRollOutL=0.3914, mouthLowerLipRollOutR=0.1068, mouthLowerLipTowardsTeethR=0.0589, mouthPressDR=0.0366, mouthPressUL=0.0938, neckDigastricDown=0.0397, neckDigastricUp=0.0295, neckStretchL=0.0654, neckStretchR=0.0578, neckSwallowPh2=0.0259 |
| MouthLowerDownRight | weighted_sum | 0.909 | jawChinCompressL=0.0412, jawChinRaiseDL=0.1129, jawChinRaiseUR=0.0392, mouthCheekBlowL=0.0867, mouthCheekSuckR=0.0245, mouthCornerSharpenDL=0.4854, mouthCornerSharpenDR=0.3455, mouthDown=0.0881, mouthFunnelDR=0.184, mouthLipsPressR=0.1088, mouthLipsStickyLPh1=0.0537, mouthLipsStickyRPh1=0.0373, mouthLipsThickDR=0.03, mouthLipsThinInwardDL=0.0292, mouthLipsThinInwardDR=0.0608, mouthLowerLipDepressR=0.4993, mouthLowerLipRollOutL=0.0637, mouthLowerLipRollOutR=0.3416, mouthLowerLipShiftRight=0.1412, mouthLowerLipTowardsTeethL=0.0494, mouthPressDL=0.028, mouthPressUR=0.0405, neckDigastricDown=0.0517, neckDigastricUp=0.0285, neckStretchL=0.0702, neckStretchR=0.0576, neckSwallowPh2=0.0292, neckThroatUp=0.0212, noseNostrilDepressR=0.1269 |
| MouthUpperUpLeft | weighted_sum | 0.8627 | jawChinRaiseUL=0.0244, mouthFunnelUL=0.0543, mouthLowerLipBiteL=0.0275, mouthPressDL=0.0345, mouthUpperLipRaiseL=0.4644, mouthUpperLipRollOutL=0.3715, mouthUpperLipShiftLeft=0.084, mouthUpperLipTowardsTeethR=0.0404, noseNasolabialDeepenL=0.2375, noseNasolabialDeepenR=0.0279 |
| MouthUpperUpRight | weighted_sum | 0.8356 | jawChinRaiseUR=0.0261, mouthFunnelUR=0.0413, mouthLowerLipBiteR=0.0456, mouthPressDR=0.0326, mouthUpperLipRaiseR=0.4298, mouthUpperLipRollOutR=0.4098, mouthUpperLipShiftRight=0.2086, mouthUpperLipTowardsTeethL=0.0381, noseNasolabialDeepenL=0.0479, noseNasolabialDeepenR=0.2428 |
| BrowDownLeft | weighted_sum | 0.9664 | browDownL=0.9957, browLateralL=0.0828, sdk:eyeFaceScrunchL:BrowDownLeft=0.3592, jawClenchL=0.0231 |
| BrowDownRight | weighted_sum | 0.9852 | browDownR=1.0216, browLateralR=0.0836, sdk:eyeFaceScrunchR:BrowDownRight=0.9655, eyeLowerLidDownR=0.0238, jawClenchR=0.0249 |
| BrowInnerUp | weighted_sum | 0.3678 | browLateralR=0.1696, browRaiseInL=0.0389 |
| BrowOuterUpLeft | weighted_sum | 0.9965 | browRaiseInL=0.3316, browRaiseOuterL=0.6403 |
| BrowOuterUpRight | weighted_sum | 0.9963 | browRaiseInR=0.3129, browRaiseOuterR=0.6565 |
| CheekPuff | weighted_sum | 0.9569 | mouthCheekBlowL=0.381, mouthCheekBlowR=0.3947, mouthLipsBlowL=0.0763, mouthLipsBlowR=0.0733 |
| CheekSquintLeft | weighted_sum | 0.9981 | eyeCheekRaiseL=0.9124, eyeFaceScrunchL=0.7088, eyeLowerLidUpL=0.1092, eyeRelaxL=0.0299, mouthCheekSuckL=0.0361, noseNasolabialDeepenL=0.0394 |
| CheekSquintRight | weighted_sum | 0.9972 | browLateralL=0.033, eyeCheekRaiseR=0.9146, eyeFaceScrunchR=0.6628, eyeLowerLidUpR=0.1076, eyeRelaxR=0.0403, mouthCheekSuckR=0.022 |
| NoseSneerLeft | weighted_sum | 0.9812 | browRaiseOuterL=0.0334, mouthSharpCornerPullL=0.075, noseNasolabialDeepenL=0.0742, noseWrinkleL=0.8926 |
| NoseSneerRight | weighted_sum | 0.9902 | browRaiseOuterR=0.0273, mouthSharpCornerPullR=0.0341, noseNasolabialDeepenR=0.0516, noseWrinkleR=0.9292 |
| TongueOut | weighted_sum | 0.8559 | browLateralL=0.0215, tongueBendUp=0.0978, tongueIn=0.058, sdk:tongueOut:TongueOut=1.1085, tongueRight=0.1229, tongueThin=0.0338, tongueTipRight=0.0506, tongueTipUp=0.3411 |
| MouthClose | iphone-calibrated | 0.6574 | mouthLipsTogetherDL+mouthLipsTogetherDR=0.0445, mouthLipsThickDL+mouthLipsThickDR=0.2712, mouthLipsPurseUL+mouthLipsPurseUR=0.0587, mouthCornerDownL+mouthCornerDownR=0.315, mouthLipsPressL+mouthLipsPressR=0.5418 |
