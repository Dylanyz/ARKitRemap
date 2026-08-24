# P2 definition score — RM_MHA_to_ARKit.json on the arkittest take

- vs per-frame BVLS solve: mean Pearson **0.943** (how faithfully the static graph reproduces the solver)
- vs mirrored iPhone reference: mean Pearson **0.6403** (end-to-end quality; solver itself scored 0.576)
- MouthClose vs iPhone: {'pearson': 0.8109, 'rmse': 0.0674, 'p95': 0.3243, 'refP95': 0.3195}

| curve | vs iPhone r | rmse | def p95 | iphone p95 |
|---|---|---|---|---|
| EyeLookOutRight | 0.99 | 0.0363 | 0.8509 | 0.8854 |
| EyeLookOutLeft | 0.9861 | 0.0525 | 0.9896 | 1.0 |
| EyeLookInLeft | 0.9847 | 0.0473 | 0.886 | 0.9617 |
| JawOpen | 0.9568 | 0.0944 | 0.9959 | 0.9613 |
| BrowDownRight | 0.95 | 0.205 | 1.0538 | 0.7881 |
| BrowDownLeft | 0.9493 | 0.1907 | 1.1539 | 0.7883 |
| EyeLookInRight | 0.9433 | 0.0995 | 0.9899 | 1.0 |
| BrowOuterUpLeft | 0.9286 | 0.1574 | 0.9302 | 0.7176 |
| MouthSmileLeft | 0.9186 | 0.1513 | 0.6626 | 0.8961 |
| BrowOuterUpRight | 0.9167 | 0.1527 | 0.9054 | 0.7171 |
| EyeBlinkRight | 0.8894 | 0.1196 | 0.7279 | 0.8928 |
| CheekSquintLeft | 0.8587 | 0.2719 | 0.9106 | 0.2961 |
| MouthPucker | 0.8465 | 0.1472 | 0.2432 | 0.1881 |
| MouthLowerDownRight | 0.8335 | 0.2259 | 0.5418 | 0.8911 |
| MouthLowerDownLeft | 0.833 | 0.2183 | 0.5611 | 0.8925 |
| EyeLookDownLeft | 0.83 | 0.1266 | 0.4703 | 0.2186 |
| EyeLookDownRight | 0.8283 | 0.1282 | 0.4817 | 0.2185 |
| MouthSmileRight | 0.8265 | 0.1979 | 0.6741 | 0.8861 |
| MouthClose | 0.8109 | 0.0674 | 0.3243 | 0.3195 |
| NoseSneerLeft | 0.8043 | 0.1261 | 0.5242 | 0.728 |
| EyeWideLeft | 0.8014 | 0.2515 | 0.6936 | 0.8738 |
| EyeLookUpRight | 0.791 | 0.133 | 0.5072 | 0.503 |
| EyeWideRight | 0.7875 | 0.2297 | 0.7685 | 0.8739 |
| EyeLookUpLeft | 0.7874 | 0.1352 | 0.5153 | 0.5041 |
| MouthUpperUpLeft | 0.7782 | 0.1132 | 0.3882 | 0.4151 |
| MouthUpperUpRight | 0.7764 | 0.0947 | 0.3414 | 0.3982 |
| NoseSneerRight | 0.752 | 0.1438 | 0.5659 | 0.695 |
| EyeSquintLeft | 0.7379 | 0.212 | 0.6572 | 0.9041 |
| MouthRollLower | 0.729 | 0.0582 | 0.1285 | 0.0163 |
| EyeBlinkLeft | 0.7221 | 0.1765 | 0.7047 | 0.8927 |
| CheekSquintRight | 0.6696 | 0.2341 | 0.7981 | 0.2799 |
| MouthFrownRight | 0.6265 | 0.2223 | 0.4365 | 0.1663 |
| EyeSquintRight | 0.6251 | 0.2341 | 0.5086 | 0.9043 |
| MouthFrownLeft | 0.6126 | 0.2154 | 0.4669 | 0.1928 |
| MouthShrugUpper | 0.5358 | 0.0958 | 0.1976 | 0.3035 |
| MouthFunnel | 0.5313 | 0.101 | 0.2892 | 0.2051 |
| MouthStretchLeft | 0.4506 | 0.2297 | 0.6422 | 0.486 |
| MouthStretchRight | 0.4349 | 0.2372 | 0.6377 | 0.4645 |
| MouthDimpleLeft | 0.3946 | 0.1086 | 0.2754 | 0.0946 |
| MouthDimpleRight | 0.3593 | 0.1085 | 0.2837 | 0.1133 |
| MouthRollUpper | 0.1978 | 0.1009 | 0.1859 | 0.1623 |
| JawForward | 0.1885 | 0.0814 | 0.1102 | 0.1779 |
| JawRight | 0.0941 | 0.0465 | 0.1057 | 0.0 |
| TongueOut | -0.0195 | 0.0755 | 0.1202 | 0.0009 |
| JawLeft | -0.0487 | 0.0495 | 0.0775 | 0.0274 |
| MouthRight | -0.1383 | 0.0643 | 0.0506 | 0.075 |
| BrowInnerUp | -0.1558 | 0.3519 | 0.1227 | 0.8074 |
| MouthLeft | -0.1718 | 0.0965 | 0.086 | 0.0876 |
