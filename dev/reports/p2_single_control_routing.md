# P2 single-control routing — solved ARKit weights at control = 1.0

Draft of the definition's input->output routing, straight from the
deformation-space solve. `residual` is the share of the control's
deformation the ARKit basis cannot express.

| control | top ARKit weights | residual |
|---|---|---|
| browDownL | BrowDownLeft=0.989 | 0.022 |
| browDownR | BrowDownRight=0.999 | 0.028 |
| browLateralL | BrowDownLeft=0.468, BrowInnerUp=0.075 | 0.794 |
| browLateralR | BrowDownRight=0.476, BrowInnerUp=0.061 | 0.811 |
| browRaiseInL | BrowInnerUp=0.320, BrowOuterUpLeft=0.314, EyeLookUpLeft=0.041 | 0.628 |
| browRaiseInR | BrowOuterUpRight=0.305, BrowInnerUp=0.294, EyeLookUpRight=0.046 | 0.649 |
| browRaiseOuterL | BrowOuterUpLeft=0.600, NoseSneerLeft=0.051, EyeWideLeft=0.027 | 0.653 |
| browRaiseOuterR | BrowOuterUpRight=0.617, NoseSneerRight=0.047, EyeWideRight=0.031 | 0.621 |
| earUpL | — | 0.999 |
| earUpR | — | 0.999 |
| eyeBlinkL | EyeBlinkLeft=1.000 | 0.000 |
| eyeBlinkR | EyeBlinkRight=1.000 | 0.000 |
| eyeLidPressL | — | 1.000 |
| eyeLidPressR | — | 0.000 |
| eyeWidenL | EyeWideLeft=1.000 | 0.000 |
| eyeWidenR | EyeWideRight=1.000 | 0.000 |
| eyeSquintInnerL | EyeSquintLeft=1.000 | 0.000 |
| eyeSquintInnerR | EyeSquintRight=1.000 | 0.000 |
| eyeCheekRaiseL | CheekSquintLeft=0.998 | 0.010 |
| eyeCheekRaiseR | CheekSquintRight=1.000 | 0.010 |
| eyeFaceScrunchL | BrowDownLeft=1.000, CheekSquintLeft=0.600, EyeWideLeft=0.446 | 0.739 |
| eyeFaceScrunchR | BrowDownRight=1.000, CheekSquintRight=0.654, EyeWideRight=0.507 | 0.727 |
| eyeUpperLidUpL | EyeWideLeft=1.000, EyeSquintLeft=0.038, EyeLookUpLeft=0.034 | 0.191 |
| eyeUpperLidUpR | EyeWideRight=1.000, EyeSquintRight=0.045, EyeLookUpRight=0.033 | 0.179 |
| eyeRelaxL | EyeBlinkLeft=0.312, EyeLookDownLeft=0.058, CheekSquintLeft=0.030 | 0.441 |
| eyeRelaxR | EyeBlinkRight=0.314, EyeLookDownRight=0.059, CheekSquintRight=0.040 | 0.445 |
| eyeLowerLidUpL | EyeSquintLeft=0.349, CheekSquintLeft=0.109, EyeLookUpLeft=0.074 | 0.714 |
| eyeLowerLidUpR | EyeSquintRight=0.404, CheekSquintRight=0.108, EyeLookUpRight=0.065 | 0.646 |
| eyeLowerLidDownL | EyeWideLeft=0.428, EyeLookUpLeft=0.402, EyeLookDownLeft=0.378 | 0.772 |
| eyeLowerLidDownR | EyeWideRight=0.386, EyeLookUpRight=0.369, EyeLookDownRight=0.352 | 0.780 |
| eyeLookUpL | EyeLookUpLeft=1.000 | 0.000 |
| eyeLookUpR | EyeLookUpRight=1.000 | 0.000 |
| eyeLookDownL | EyeLookDownLeft=1.000 | 0.000 |
| eyeLookDownR | EyeLookDownRight=1.000 | 0.000 |
| eyeLookLeftL | EyeLookOutLeft=1.000 | 0.000 |
| eyeLookLeftR | EyeLookInRight=1.000 | 0.000 |
| eyeLookRightL | EyeLookInLeft=1.000 | 0.000 |
| eyeLookRightR | EyeLookOutRight=1.000 | 0.000 |
| eyePupilWideL | — | 1.000 |
| eyePupilWideR | — | 1.000 |
| eyePupilNarrowL | — | 1.000 |
| eyePupilNarrowR | — | 1.000 |
| eyeParallelLookDirection | EyeWideLeft=0.201, EyeWideRight=0.153, EyeSquintLeft=0.104 | 0.895 |
| eyelashesUpINL | EyeWideLeft=0.910, EyeBlinkLeft=0.362 | 0.986 |
| eyelashesUpINR | EyeWideRight=0.638, EyeBlinkRight=0.257 | 0.994 |
| eyelashesUpOUTL | EyeWideLeft=0.914, EyeBlinkLeft=0.364 | 0.991 |
| eyelashesUpOUTR | EyeWideRight=1.000, EyeBlinkRight=0.479, EyeLookUpRight=0.049 | 0.980 |
| eyelashesDownINL | — | 1.000 |
| eyelashesDownINR | — | 1.000 |
| eyelashesDownOUTL | — | 1.000 |
| eyelashesDownOUTR | — | 1.000 |
| noseWrinkleL | NoseSneerLeft=0.880, MouthUpperUpLeft=0.076, BrowOuterUpLeft=0.048 | 0.266 |
| noseWrinkleR | NoseSneerRight=0.893, MouthUpperUpRight=0.068, BrowInnerUp=0.040 | 0.251 |
| noseWrinkleUpperL | — | 0.000 |
| noseWrinkleUpperR | — | 0.000 |
| noseNostrilDepressL | MouthRollUpper=0.055, MouthPressLeft=0.041, MouthLowerDownLeft=0.037 | 0.906 |
| noseNostrilDepressR | MouthRollUpper=0.055, MouthPressRight=0.037, EyeSquintRight=0.023 | 0.888 |
| noseNostrilDilateL | — | 0.993 |
| noseNostrilDilateR | — | 0.991 |
| noseNostrilCompressL | — | 0.996 |
| noseNostrilCompressR | MouthUpperUpRight=0.028 | 0.990 |
| noseNasolabialDeepenL | MouthUpperUpLeft=0.243, NoseSneerLeft=0.075, MouthUpperUpRight=0.055 | 0.796 |
| noseNasolabialDeepenR | MouthUpperUpRight=0.205, MouthUpperUpLeft=0.050, NoseSneerRight=0.039 | 0.786 |
| mouthCheekSuckL | MouthShrugUpper=0.098, CheekSquintLeft=0.036, MouthPucker=0.026 | 0.991 |
| mouthCheekSuckR | MouthShrugUpper=0.101, MouthPucker=0.038, MouthLowerDownRight=0.025 | 0.990 |
| mouthCheekBlowL | CheekPuff=0.326, MouthDimpleRight=0.270, MouthStretchRight=0.241 | 0.743 |
| mouthCheekBlowR | CheekPuff=0.340, MouthDimpleLeft=0.309, MouthStretchLeft=0.275 | 0.753 |
| mouthLipsBlowL | MouthLowerDownLeft=0.194, MouthPucker=0.127, MouthStretchRight=0.084 | 0.912 |
| mouthLipsBlowR | MouthPucker=0.147, MouthLowerDownRight=0.136, MouthStretchLeft=0.076 | 0.910 |
| mouthLeft | MouthLeft=1.000 | 0.000 |
| mouthRight | MouthRight=1.000 | 0.000 |
| mouthUp | MouthShrugUpper=0.168, MouthShrugLower=0.156, MouthDimpleRight=0.040 | 0.844 |
| mouthDown | MouthFrownLeft=0.124, MouthFrownRight=0.104, MouthLowerDownLeft=0.099 | 0.908 |
| mouthUpperLipRaiseL | MouthUpperUpLeft=1.000 | 0.000 |
| mouthUpperLipRaiseR | MouthUpperUpRight=1.000 | 0.000 |
| mouthLowerLipDepressL | MouthLowerDownLeft=1.000 | 0.000 |
| mouthLowerLipDepressR | MouthLowerDownRight=1.000 | 0.000 |
| mouthCornerPullL | MouthSmileLeft=1.000 | 0.000 |
| mouthCornerPullR | MouthSmileRight=0.999 | 0.001 |
| mouthStretchL | MouthStretchLeft=1.000 | 0.000 |
| mouthStretchR | MouthStretchRight=1.000 | 0.000 |
| mouthStretchLipsCloseL | — | 0.000 |
| mouthStretchLipsCloseR | — | 0.000 |
| mouthDimpleL | MouthDimpleLeft=1.000 | 0.000 |
| mouthDimpleR | MouthDimpleRight=1.000 | 0.000 |
| mouthCornerDepressL | MouthFrownLeft=1.000 | 0.000 |
| mouthCornerDepressR | MouthFrownRight=1.000 | 0.000 |
| mouthPressUL | MouthRollUpper=0.334, MouthLowerDownLeft=0.312, MouthPressLeft=0.258 | 0.543 |
| mouthPressUR | MouthRollUpper=0.370, MouthPressRight=0.245, MouthLowerDownRight=0.211 | 0.530 |
| mouthPressDL | MouthPressLeft=0.455, MouthShrugLower=0.297, MouthFrownLeft=0.156 | 0.530 |
| mouthPressDR | MouthPressRight=0.422, MouthShrugLower=0.315, MouthLowerDownLeft=0.188 | 0.535 |
| mouthLipsPurseUL | MouthPucker=0.136, MouthStretchRight=0.055, MouthShrugUpper=0.031 | 0.890 |
| mouthLipsPurseUR | MouthPucker=0.128, MouthStretchLeft=0.044, MouthPressRight=0.033 | 0.889 |
| mouthLipsPurseDL | MouthLowerDownLeft=0.164, MouthPucker=0.130, MouthStretchRight=0.063 | 0.872 |
| mouthLipsPurseDR | MouthPucker=0.121, MouthLowerDownRight=0.121, MouthStretchLeft=0.051 | 0.888 |
| mouthLipsTowardsUL | MouthPucker=0.139, MouthShrugLower=0.078, MouthUpperUpLeft=0.055 | 0.907 |
| mouthLipsTowardsUR | MouthPucker=0.143, MouthShrugLower=0.081, MouthUpperUpRight=0.065 | 0.896 |
| mouthLipsTowardsDL | MouthLowerDownLeft=0.221, MouthPucker=0.158, MouthShrugLower=0.088 | 0.790 |
| mouthLipsTowardsDR | MouthLowerDownRight=0.161, MouthPucker=0.143, MouthFunnel=0.088 | 0.796 |
| mouthFunnelUL | MouthUpperUpLeft=0.331, MouthPucker=0.104, MouthFunnel=0.070 | 0.751 |
| mouthFunnelUR | MouthUpperUpRight=0.316, MouthPucker=0.102, MouthShrugUpper=0.087 | 0.746 |
| mouthFunnelDL | MouthLowerDownLeft=0.907, MouthFunnel=0.201, MouthLowerDownRight=0.115 | 0.616 |
| mouthFunnelDR | MouthLowerDownRight=0.805, MouthFunnel=0.215, MouthPucker=0.077 | 0.632 |
| mouthLipsTogetherUL | — | 0.000 |
| mouthLipsTogetherUR | — | 0.000 |
| mouthLipsTogetherDL | — | 0.000 |
| mouthLipsTogetherDR | — | 0.000 |
| mouthUpperLipBiteL | MouthRollUpper=0.573, MouthLowerDownLeft=0.259, MouthPressLeft=0.192 | 0.531 |
| mouthUpperLipBiteR | MouthRollUpper=0.583, MouthPressRight=0.214, MouthLowerDownRight=0.198 | 0.508 |
| mouthLowerLipBiteL | MouthPressLeft=0.426, MouthShrugLower=0.294, MouthRollLower=0.237 | 0.570 |
| mouthLowerLipBiteR | MouthPressRight=0.428, MouthShrugLower=0.300, MouthRollLower=0.236 | 0.570 |
| mouthLipsTightenUL | MouthRollUpper=0.060, MouthShrugUpper=0.051, MouthFrownLeft=0.037 | 0.860 |
| mouthLipsTightenUR | MouthRollUpper=0.052, MouthShrugUpper=0.029, MouthPressRight=0.021 | 0.923 |
| mouthLipsTightenDL | MouthPressLeft=0.034, MouthShrugLower=0.022 | 0.916 |
| mouthLipsTightenDR | MouthPressRight=0.047, MouthFrownRight=0.035 | 0.891 |
| mouthLipsPressL | MouthDimpleLeft=0.280, MouthFrownLeft=0.230, MouthPucker=0.059 | 0.847 |
| mouthLipsPressR | MouthDimpleRight=0.400, MouthFrownRight=0.290, MouthLowerDownRight=0.144 | 0.750 |
| mouthSharpCornerPullL | MouthSmileLeft=0.533, MouthDimpleLeft=0.102, MouthUpperUpLeft=0.087 | 0.411 |
| mouthSharpCornerPullR | MouthSmileRight=0.545, MouthDimpleRight=0.096, MouthUpperUpRight=0.076 | 0.423 |
| mouthStickyUC | — | 0.998 |
| mouthStickyUINL | — | 0.999 |
| mouthStickyUINR | — | 0.998 |
| mouthStickyUOUTL | — | 0.997 |
| mouthStickyUOUTR | — | 0.996 |
| mouthStickyDC | — | 0.994 |
| mouthStickyDINL | — | 0.992 |
| mouthStickyDINR | — | 0.996 |
| mouthStickyDOUTL | — | 0.996 |
| mouthStickyDOUTR | — | 0.992 |
| mouthLipsStickyLPh1 | MouthLowerDownRight=0.054, MouthShrugLower=0.046, MouthLowerDownLeft=0.027 | 0.994 |
| mouthLipsStickyLPh2 | MouthShrugLower=0.043, MouthPucker=0.024 | 0.993 |
| mouthLipsStickyLPh3 | MouthShrugLower=0.039 | 0.996 |
| mouthLipsStickyRPh1 | MouthLowerDownLeft=0.062, MouthShrugLower=0.041, MouthLowerDownRight=0.037 | 0.995 |
| mouthLipsStickyRPh2 | MouthShrugLower=0.035, MouthPucker=0.027 | 0.996 |
| mouthLipsStickyRPh3 | MouthShrugLower=0.027, MouthPucker=0.024 | 0.997 |
| mouthLipsPushUL | MouthFrownLeft=0.028 | 0.973 |
| mouthLipsPushUR | MouthFrownRight=0.038 | 0.972 |
| mouthLipsPushDL | MouthLowerDownRight=0.042, MouthLowerDownLeft=0.029, MouthFunnel=0.024 | 0.930 |
| mouthLipsPushDR | MouthLowerDownLeft=0.044, MouthFunnel=0.029 | 0.931 |
| mouthLipsPullUL | MouthShrugUpper=0.072, MouthRollUpper=0.035, MouthStretchLeft=0.025 | 0.948 |
| mouthLipsPullUR | MouthShrugUpper=0.064, MouthRollUpper=0.039, MouthStretchRight=0.031 | 0.941 |
| mouthLipsPullDL | — | 0.953 |
| mouthLipsPullDR | MouthStretchRight=0.023 | 0.946 |
| mouthLipsThinUL | MouthFrownLeft=0.039, MouthDimpleLeft=0.031 | 0.959 |
| mouthLipsThinUR | MouthFrownRight=0.024 | 0.966 |
| mouthLipsThinDL | MouthStretchLeft=0.034, MouthStretchRight=0.022 | 0.966 |
| mouthLipsThinDR | MouthStretchRight=0.034, MouthStretchLeft=0.021 | 0.962 |
| mouthLipsThickUL | — | 0.983 |
| mouthLipsThickUR | — | 0.983 |
| mouthLipsThickDL | MouthLowerDownLeft=0.126, MouthFunnel=0.053, MouthShrugLower=0.052 | 0.908 |
| mouthLipsThickDR | MouthLowerDownRight=0.142, MouthFunnel=0.060, MouthShrugLower=0.060 | 0.899 |
| mouthLipsThinInwardUL | MouthShrugUpper=0.047, MouthFrownLeft=0.031 | 0.955 |
| mouthLipsThinInwardUR | MouthShrugUpper=0.054, MouthFrownRight=0.027 | 0.958 |
| mouthLipsThinInwardDL | MouthLowerDownRight=0.029, MouthFrownLeft=0.021 | 0.953 |
| mouthLipsThinInwardDR | MouthLowerDownRight=0.061, MouthLowerDownLeft=0.036, MouthFrownRight=0.023 | 0.951 |
| mouthLipsThickInwardUL | — | 0.986 |
| mouthLipsThickInwardUR | — | 0.989 |
| mouthLipsThickInwardDL | — | 0.986 |
| mouthLipsThickInwardDR | — | 0.991 |
| mouthCornerSharpenUL | MouthShrugLower=0.034, MouthRollUpper=0.027, MouthFunnel=0.024 | 0.988 |
| mouthCornerSharpenUR | MouthShrugLower=0.036, MouthFunnel=0.029, JawRight=0.026 | 0.989 |
| mouthCornerSharpenDL | MouthLowerDownLeft=0.412, MouthLowerDownRight=0.278, MouthShrugLower=0.086 | 0.928 |
| mouthCornerSharpenDR | MouthLowerDownRight=0.267, MouthLowerDownLeft=0.179, MouthShrugLower=0.080 | 0.947 |
| mouthCornerRounderUL | MouthLowerDownLeft=0.024 | 0.969 |
| mouthCornerRounderUR | MouthStretchRight=0.025 | 0.967 |
| mouthCornerRounderDL | MouthFrownLeft=0.040 | 0.956 |
| mouthCornerRounderDR | MouthFrownRight=0.043 | 0.941 |
| mouthUpperLipTowardsTeethL | MouthUpperUpRight=0.038, MouthRollUpper=0.037 | 0.955 |
| mouthUpperLipTowardsTeethR | MouthUpperUpLeft=0.040, MouthRollUpper=0.039 | 0.950 |
| mouthLowerLipTowardsTeethL | MouthShrugLower=0.071, MouthLowerDownRight=0.049, MouthPressLeft=0.026 | 0.891 |
| mouthLowerLipTowardsTeethR | MouthShrugLower=0.070, MouthLowerDownLeft=0.059, MouthPressRight=0.025 | 0.882 |
| mouthUpperLipShiftLeft | MouthUpperUpLeft=0.025 | 0.985 |
| mouthUpperLipShiftRight | MouthUpperUpRight=0.028 | 0.983 |
| mouthLowerLipShiftLeft | MouthLowerDownLeft=0.141, MouthStretchLeft=0.048, MouthShrugLower=0.025 | 0.906 |
| mouthLowerLipShiftRight | MouthLowerDownRight=0.128, MouthStretchRight=0.052, MouthShrugLower=0.026 | 0.908 |
| mouthUpperLipRollInL | MouthRollUpper=0.469, MouthLowerDownLeft=0.153, MouthUpperUpRight=0.122 | 0.458 |
| mouthUpperLipRollInR | MouthRollUpper=0.482, MouthLowerDownRight=0.125, MouthUpperUpLeft=0.125 | 0.444 |
| mouthUpperLipRollOutL | MouthUpperUpLeft=0.368, MouthUpperUpRight=0.138, MouthPucker=0.135 | 0.898 |
| mouthUpperLipRollOutR | MouthUpperUpRight=0.368, MouthFrownRight=0.154, MouthUpperUpLeft=0.145 | 0.898 |
| mouthLowerLipRollInL | MouthRollLower=0.300, MouthFrownLeft=0.127, MouthPressLeft=0.121 | 0.546 |
| mouthLowerLipRollInR | MouthRollLower=0.310, MouthLowerDownLeft=0.150, MouthShrugLower=0.129 | 0.551 |
| mouthLowerLipRollOutL | MouthLowerDownLeft=0.591, MouthPucker=0.173, MouthLowerDownRight=0.149 | 0.843 |
| mouthLowerLipRollOutR | MouthLowerDownRight=0.257, MouthStretchRight=0.208, MouthPucker=0.161 | 0.863 |
| mouthCornerUpL | MouthLowerDownLeft=0.033, MouthLowerDownRight=0.023 | 0.986 |
| mouthCornerUpR | — | 0.990 |
| mouthCornerDownL | MouthFrownLeft=0.050 | 0.941 |
| mouthCornerDownR | MouthFrownRight=0.044 | 0.953 |
| mouthCornerWideL | — | 0.981 |
| mouthCornerWideR | — | 0.981 |
| mouthCornerNarrowL | — | 0.993 |
| mouthCornerNarrowR | — | 0.996 |
| jawOpen | JawOpen=1.000 | 0.000 |
| jawLeft | JawLeft=1.000 | 0.000 |
| jawRight | JawRight=1.000 | 0.000 |
| jawFwd | JawForward=1.000 | 0.001 |
| jawBack | MouthLowerDownRight=0.155, MouthLowerDownLeft=0.122, JawOpen=0.087 | 0.962 |
| jawClenchL | BrowDownLeft=0.023 | 0.990 |
| jawClenchR | BrowDownRight=0.025 | 0.991 |
| jawChinRaiseDL | MouthLowerDownRight=0.706, MouthShrugLower=0.594, MouthStretchRight=0.071 | 0.793 |
| jawChinRaiseDR | MouthLowerDownLeft=0.723, MouthShrugLower=0.602, MouthStretchLeft=0.059 | 0.790 |
| jawChinRaiseUL | MouthShrugUpper=0.412, MouthUpperUpLeft=0.114, MouthPressLeft=0.030 | 0.670 |
| jawChinRaiseUR | MouthShrugUpper=0.416, MouthUpperUpRight=0.118, MouthFrownLeft=0.034 | 0.655 |
| jawChinCompressL | MouthShrugLower=0.116, MouthLowerDownRight=0.041, MouthStretchLeft=0.035 | 0.956 |
| jawChinCompressR | MouthShrugLower=0.113, MouthLowerDownLeft=0.069, JawRight=0.038 | 0.946 |
| jawOpenExtreme | — | 0.000 |
| neckStretchL | JawForward=0.102, MouthLowerDownRight=0.070, MouthLowerDownLeft=0.065 | 0.988 |
| neckStretchR | JawForward=0.109, MouthLowerDownLeft=0.058, MouthLowerDownRight=0.058 | 0.990 |
| neckSwallowPh1 | — | 0.999 |
| neckSwallowPh2 | MouthLowerDownRight=0.029, MouthLowerDownLeft=0.026 | 0.999 |
| neckSwallowPh3 | — | 0.999 |
| neckSwallowPh4 | — | 0.999 |
| neckMastoidContractL | — | 1.000 |
| neckMastoidContractR | — | 1.000 |
| neckThroatDown | JawForward=0.030 | 0.996 |
| neckThroatUp | MouthShrugLower=0.028, MouthLowerDownRight=0.021 | 0.999 |
| neckDigastricDown | MouthLowerDownRight=0.052, MouthLowerDownLeft=0.040, JawOpen=0.037 | 0.978 |
| neckDigastricUp | MouthShrugLower=0.081, MouthLowerDownLeft=0.029, MouthLowerDownRight=0.028 | 0.985 |
| neckThroatExhale | — | 1.000 |
| neckThroatInhale | — | 1.000 |
| teethUpU | — | 1.000 |
| teethUpD | — | 1.000 |
| teethDownU | — | 1.000 |
| teethDownD | — | 1.000 |
| teethLeftU | — | 1.000 |
| teethLeftD | — | 1.000 |
| teethRightU | — | 1.000 |
| teethRightD | — | 1.000 |
| teethFwdU | — | 1.000 |
| teethFwdD | — | 1.000 |
| teethBackU | — | 1.000 |
| teethBackD | — | 1.000 |
| tongueUp | — | 1.000 |
| tongueDown | TongueOut=0.117 | 0.774 |
| tongueLeft | — | 1.000 |
| tongueRight | TongueOut=0.113 | 0.992 |
| tongueOut | TongueOut=1.000 | 0.297 |
| tongueIn | TongueOut=0.219 | 0.869 |
| tongueBendUp | TongueOut=0.098 | 0.992 |
| tongueBendDown | — | 1.000 |
| tongueTwistLeft | — | 1.000 |
| tongueTwistRight | — | 1.000 |
| tongueTipUp | TongueOut=0.225 | 0.948 |
| tongueTipDown | — | 1.000 |
| tongueTipLeft | — | 1.000 |
| tongueTipRight | TongueOut=0.050 | 0.997 |
| tongueWide | TongueOut=0.107 | 0.955 |
| tongueNarrow | — | 1.000 |
| tonguePress | — | 1.000 |
| tongueRoll | — | 1.000 |
| tongueThick | — | 0.999 |
| tongueThin | TongueOut=0.034 | 0.982 |
