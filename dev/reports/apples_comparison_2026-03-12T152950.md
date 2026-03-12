# Apples-to-Apples Comparison Report

**Generated:** 2026-03-12T152950  
**A:** `/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/AS_MP_VecDemo1-OnMH` (MHA ground truth, 1450 frames)  
**B:** `/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/AS_MP_VecDemo1-allkeys_ARKit_OnMH` (remap round-trip, 1450 frames)  
**C:** `/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/Vec-ARKITBAKED-T34_60fps-02_OnMH` (real iPhone ARKit, 1449 frames)  
**Common frames for comparison:** 1449  

## Family-Level MSE Summary

| Family | A vs B (mean MSE) | A vs C (mean MSE) | B vs C (mean MSE) | # Curves |
|--------|-------------------|--------------------|--------------------|----------|
| jaw | 0.012562 | 0.026310 | 0.032729 | 8 |
| mouth | 0.042567 | 0.084055 | 0.066584 | 42 |
| brow | 0.018840 | 0.245168 | 0.196427 | 8 |
| eye | 0.000000 | 0.076614 | 0.076614 | 16 |
| nose | 0.000000 | 0.027757 | 0.027757 | 2 |
| tongue | 0.104748 | 0.197611 | 0.071759 | 4 |

## Top 20 Round-Trip Error Curves (A vs B)

| Curve | MSE | Max Diff | Family |
|-------|-----|----------|--------|
| ctrl_expressions_mouthlipstogetherdr | 0.451615 | 1.0000 | mouth |
| ctrl_expressions_mouthlipstogetherdl | 0.451138 | 1.0000 | mouth |
| ctrl_expressions_mouthlipstogetherul | 0.301719 | 1.0000 | mouth |
| ctrl_expressions_mouthlipstogetherur | 0.300804 | 0.9996 | mouth |
| ctrl_expressions_tonguewide | 0.254072 | 0.7726 | tongue |
| ctrl_expressions_tongueout | 0.122360 | 0.6448 | tongue |
| ctrl_expressions_jawopen | 0.100493 | 0.6263 | jaw |
| ctrl_expressions_mouthfunnelul | 0.076366 | 0.6248 | mouth |
| ctrl_expressions_mouthfunnelur | 0.071910 | 0.6210 | mouth |
| ctrl_expressions_browraiseinl | 0.058659 | 0.4527 | brow |
| ctrl_expressions_browraiseinr | 0.057098 | 0.4092 | brow |
| ctrl_expressions_tonguedown | 0.041573 | 0.3184 | tongue |
| ctrl_expressions_mouthfunneldr | 0.036748 | 0.4631 | mouth |
| ctrl_expressions_mouthfunneldl | 0.032287 | 0.4602 | mouth |
| ctrl_expressions_browraiseouterl | 0.015523 | 0.2416 | brow |
| ctrl_expressions_browraiseouterr | 0.014775 | 0.2129 | brow |
| ctrl_expressions_mouthlipstowardsur | 0.012997 | 0.3902 | mouth |
| ctrl_expressions_mouthlipstowardsul | 0.010680 | 0.3697 | mouth |
| ctrl_expressions_mouthlipstowardsdr | 0.008818 | 0.2689 | mouth |
| ctrl_expressions_mouthlipstowardsdl | 0.008678 | 0.2654 | mouth |

## Top 20 MHA vs iPhone ARKit Curves (A vs C)

| Curve | MSE | Max Diff | Family |
|-------|-----|----------|--------|
| ctrl_expressions_tonguewide | 0.580964 | 1.0000 | tongue |
| ctrl_expressions_browlaterall | 0.489245 | 0.9929 | brow |
| ctrl_expressions_browlateralr | 0.433058 | 0.9381 | brow |
| ctrl_expressions_browraiseinr | 0.416533 | 1.0845 | brow |
| ctrl_expressions_browraiseinl | 0.394770 | 1.0835 | brow |
| ctrl_expressions_mouthlipstogetherdr | 0.367024 | 1.0000 | mouth |
| ctrl_expressions_mouthlipstogetherdl | 0.366111 | 1.0000 | mouth |
| ctrl_expressions_mouthfunnelul | 0.312360 | 1.1850 | mouth |
| ctrl_expressions_mouthfunnelur | 0.306201 | 1.1857 | mouth |
| ctrl_expressions_mouthlipstogetherul | 0.248687 | 1.0000 | mouth |
| ctrl_expressions_mouthlipstogetherur | 0.248247 | 1.0000 | mouth |
| ctrl_expressions_tonguedown | 0.209476 | 1.0000 | tongue |
| ctrl_expressions_eyesquintinnerr | 0.171496 | 1.0000 | eye |
| ctrl_expressions_mouthfunneldl | 0.168515 | 1.1632 | mouth |
| ctrl_expressions_mouthfunneldr | 0.168330 | 1.1636 | mouth |
| ctrl_expressions_mouthlowerlipdepressl | 0.161564 | 0.9873 | mouth |
| ctrl_expressions_mouthlowerlipdepressr | 0.159842 | 0.9922 | mouth |
| ctrl_expressions_eyelookupl | 0.155616 | 0.8035 | eye |
| ctrl_expressions_mouthlipspurseul | 0.153475 | 0.8143 | mouth |
| ctrl_expressions_mouthlipspurseur | 0.152283 | 0.8375 | mouth |

## Frame 0

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_mouthlipstogetherur | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| ctrl_expressions_mouthlipstogetherul | 0.0069 | 0.0000 | 1.0000 | 0.0069 | 0.9931 | 1.0000 |
| ctrl_expressions_eyesquintinnerr | 1.0000 | 1.0000 | 0.1442 | 0.0000 | 0.8558 | 0.8558 |
| ctrl_expressions_eyesquintinnerl | 1.0000 | 1.0000 | 0.1453 | 0.0000 | 0.8547 | 0.8547 |
| ctrl_expressions_mouthlipstogetherdl | 0.1724 | 0.0000 | 1.0000 | 0.1724 | 0.8276 | 1.0000 |
| ctrl_expressions_mouthlipstogetherdr | 0.1724 | 0.0000 | 1.0000 | 0.1724 | 0.8276 | 1.0000 |
| ctrl_expressions_mouthlipspursedr | 0.7129 | 0.6242 | 0.0337 | 0.0887 | 0.6791 | 0.5905 |
| ctrl_expressions_mouthlipspursedl | 0.6978 | 0.6242 | 0.0337 | 0.0735 | 0.6640 | 0.5905 |
| ctrl_expressions_mouthlipspurseul | 0.6582 | 0.6242 | 0.0337 | 0.0340 | 0.6245 | 0.5905 |
| ctrl_expressions_mouthlipspurseur | 0.6577 | 0.6242 | 0.0337 | 0.0335 | 0.6240 | 0.5905 |
| ctrl_expressions_mouthupperlipraiser | 0.5898 | 0.5898 | 0.0110 | 0.0000 | 0.5789 | 0.5789 |
| ctrl_expressions_tonguedown | 0.5521 | 0.2508 | 0.0000 | 0.3014 | 0.5521 | 0.2508 |
| ctrl_expressions_mouthupperlipraisel | 0.5371 | 0.5371 | 0.0131 | 0.0000 | 0.5240 | 0.5240 |
| ctrl_expressions_nosewrinkler | 0.7676 | 0.7676 | 0.2450 | 0.0000 | 0.5225 | 0.5225 |
| ctrl_expressions_browraiseinr | 0.3811 | 0.7871 | 0.8924 | 0.4060 | 0.5113 | 0.1053 |
| ctrl_expressions_browraiseinl | 0.4050 | 0.7991 | 0.8914 | 0.3940 | 0.4863 | 0.0923 |
| ctrl_expressions_browraiseouterl | 1.0000 | 0.7991 | 0.5228 | 0.2009 | 0.4772 | 0.2763 |
| ctrl_expressions_browraiseouterr | 1.0000 | 0.7871 | 0.5238 | 0.2129 | 0.4762 | 0.2633 |
| ctrl_expressions_mouthfunnelul | 0.0010 | 0.4694 | 0.1204 | 0.4684 | 0.1194 | 0.3491 |
| ctrl_expressions_mouthfunnelur | 0.0010 | 0.4694 | 0.1204 | 0.4684 | 0.1194 | 0.3491 |
| ctrl_expressions_nosewrinklel | 0.6934 | 0.6934 | 0.2802 | 0.0000 | 0.4131 | 0.4131 |
| ctrl_expressions_browlaterall | 0.0149 | 0.1134 | 0.4247 | 0.0985 | 0.4098 | 0.3113 |
| ctrl_expressions_mouthfunneldr | 0.0688 | 0.4694 | 0.1204 | 0.4006 | 0.0515 | 0.3491 |
| ctrl_expressions_mouthfunneldl | 0.0706 | 0.4694 | 0.1204 | 0.3989 | 0.0498 | 0.3491 |
| ctrl_expressions_eyelookupl | 0.3867 | 0.3867 | 0.0000 | 0.0000 | 0.3867 | 0.3867 |
| ctrl_expressions_eyelookupr | 0.3828 | 0.3828 | 0.0000 | 0.0000 | 0.3828 | 0.3828 |
| ctrl_expressions_browlateralr | 0.0127 | 0.0000 | 0.3686 | 0.0127 | 0.3559 | 0.3686 |
| ctrl_expressions_jawchinraisedr | 0.4304 | 0.4265 | 0.1347 | 0.0039 | 0.2957 | 0.2918 |
| ctrl_expressions_jawchinraisedl | 0.4226 | 0.4265 | 0.1347 | 0.0039 | 0.2879 | 0.2918 |
| ctrl_expressions_eyewidenl | 0.2666 | 0.2666 | 0.0000 | 0.0000 | 0.2666 | 0.2666 |

## Frame 276

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_tonguewide | 1.0000 | 0.5214 | 0.0000 | 0.4786 | 1.0000 | 0.5214 |
| ctrl_expressions_tonguedown | 0.9829 | 0.6858 | 0.0000 | 0.2970 | 0.9829 | 0.6858 |
| ctrl_expressions_browraiseinr | 0.6383 | 0.8719 | 1.5685 | 0.2335 | 0.9301 | 0.6966 |
| ctrl_expressions_browraiseinl | 0.7025 | 0.9039 | 1.5683 | 0.2015 | 0.8658 | 0.6643 |
| ctrl_expressions_browlaterall | 0.0081 | 0.0828 | 0.8644 | 0.0747 | 0.8563 | 0.7816 |
| ctrl_expressions_browlateralr | 0.0052 | 0.0000 | 0.8179 | 0.0052 | 0.8127 | 0.8179 |
| ctrl_expressions_mouthfunneldl | 0.0008 | 0.2411 | 0.6651 | 0.2403 | 0.6644 | 0.4240 |
| ctrl_expressions_mouthfunneldr | 0.0018 | 0.2411 | 0.6651 | 0.2393 | 0.6634 | 0.4240 |
| ctrl_expressions_mouthfunnelur | 0.0192 | 0.2411 | 0.6651 | 0.2219 | 0.6459 | 0.4240 |
| ctrl_expressions_mouthfunnelul | 0.0227 | 0.2411 | 0.6651 | 0.2184 | 0.6425 | 0.4240 |
| ctrl_expressions_tongueout | 0.0000 | 0.6385 | 0.0000 | 0.6385 | 0.0000 | 0.6385 |
| ctrl_expressions_mouthlowerlipdepressr | 0.0015 | 0.0015 | 0.6385 | 0.0000 | 0.6370 | 0.6370 |
| ctrl_expressions_mouthlowerlipdepressl | 0.0002 | 0.0002 | 0.6144 | 0.0000 | 0.6142 | 0.6142 |
| ctrl_expressions_jawopen | 0.1720 | 0.0000 | 0.7283 | 0.1720 | 0.5563 | 0.7283 |
| ctrl_expressions_eyelookupl | 0.5249 | 0.5249 | 0.0490 | 0.0000 | 0.4759 | 0.4759 |
| ctrl_expressions_eyelookupr | 0.5213 | 0.5213 | 0.0491 | 0.0000 | 0.4722 | 0.4722 |
| ctrl_expressions_jawchinraisedl | 0.4441 | 0.4434 | 0.0000 | 0.0006 | 0.4441 | 0.4434 |
| ctrl_expressions_jawchinraisedr | 0.4428 | 0.4434 | 0.0000 | 0.0006 | 0.4428 | 0.4434 |
| ctrl_expressions_mouthstretchr | 0.0014 | 0.0014 | 0.4327 | 0.0000 | 0.4313 | 0.4313 |
| ctrl_expressions_mouthlipspurseur | 0.3814 | 0.3206 | 0.0000 | 0.0608 | 0.3814 | 0.3206 |
| ctrl_expressions_mouthstretchl | 0.0140 | 0.0140 | 0.3946 | 0.0000 | 0.3806 | 0.3806 |
| ctrl_expressions_mouthlipspurseul | 0.3614 | 0.3206 | 0.0000 | 0.0408 | 0.3614 | 0.3206 |
| ctrl_expressions_mouthlipspursedl | 0.3330 | 0.3206 | 0.0000 | 0.0124 | 0.3330 | 0.3206 |
| ctrl_expressions_mouthlipspursedr | 0.3289 | 0.3206 | 0.0000 | 0.0083 | 0.3289 | 0.3206 |
| ctrl_expressions_mouthlipstogetherdl | 0.2834 | 0.0000 | 0.1994 | 0.2834 | 0.0840 | 0.1994 |
| ctrl_expressions_mouthlipstogetherdr | 0.2803 | 0.0000 | 0.1994 | 0.2803 | 0.0808 | 0.1994 |
| ctrl_expressions_eyewidenr | 0.3455 | 0.3455 | 0.6236 | 0.0000 | 0.2782 | 0.2782 |
| ctrl_expressions_mouthcornerdepressr | 0.0827 | 0.0827 | 0.3465 | 0.0000 | 0.2638 | 0.2638 |
| ctrl_expressions_mouthcornerdepressl | 0.0853 | 0.0853 | 0.3384 | 0.0000 | 0.2531 | 0.2531 |
| ctrl_expressions_browraiseouterl | 1.0000 | 0.9039 | 0.7504 | 0.0961 | 0.2496 | 0.1535 |

## Frame 362

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_tonguewide | 1.0000 | 0.2274 | 0.0000 | 0.7726 | 1.0000 | 0.2274 |
| ctrl_expressions_mouthlowerlipdepressr | 0.9922 | 0.9922 | 0.0000 | 0.0000 | 0.9922 | 0.9922 |
| ctrl_expressions_mouthlowerlipdepressl | 0.9936 | 0.9936 | 0.0064 | 0.0000 | 0.9873 | 0.9873 |
| ctrl_expressions_browraiseouterl | 0.9961 | 0.8018 | 0.3458 | 0.1943 | 0.6503 | 0.4560 |
| ctrl_expressions_mouthfunneldr | 0.6099 | 0.3772 | 0.0109 | 0.2327 | 0.5990 | 0.3663 |
| ctrl_expressions_browraiseouterr | 0.9333 | 0.7516 | 0.3466 | 0.1817 | 0.5867 | 0.4050 |
| ctrl_expressions_jawopen | 0.5684 | 0.4190 | 0.0000 | 0.1493 | 0.5684 | 0.4190 |
| ctrl_expressions_eyelookupl | 0.5619 | 0.5619 | 0.0000 | 0.0000 | 0.5619 | 0.5619 |
| ctrl_expressions_eyelookupr | 0.5584 | 0.5584 | 0.0000 | 0.0000 | 0.5584 | 0.5584 |
| ctrl_expressions_mouthfunneldl | 0.5541 | 0.3772 | 0.0109 | 0.1768 | 0.5432 | 0.3663 |
| ctrl_expressions_browraiseinl | 0.4233 | 0.8018 | 0.5462 | 0.3785 | 0.1229 | 0.2556 |
| ctrl_expressions_browraiseinr | 0.3857 | 0.7516 | 0.5470 | 0.3659 | 0.1613 | 0.2046 |
| ctrl_expressions_eyelookleftl | 0.3373 | 0.3373 | 0.0000 | 0.0000 | 0.3373 | 0.3373 |
| ctrl_expressions_eyelookleftr | 0.3046 | 0.3046 | 0.0000 | 0.0000 | 0.3046 | 0.3046 |
| ctrl_expressions_tonguedown | 0.0000 | 0.2991 | 0.0000 | 0.2991 | 0.0000 | 0.2991 |
| ctrl_expressions_eyesquintinnerr | 0.2892 | 0.2892 | 0.0000 | 0.0000 | 0.2892 | 0.2892 |
| ctrl_expressions_mouthlipspurseul | 0.2952 | 0.1841 | 0.0145 | 0.1111 | 0.2807 | 0.1696 |
| ctrl_expressions_tongueout | 0.0000 | 0.2785 | 0.0000 | 0.2785 | 0.0000 | 0.2785 |
| ctrl_expressions_mouthlipstogetherur | 0.2759 | 0.2521 | 0.0000 | 0.0238 | 0.2759 | 0.2521 |
| ctrl_expressions_mouthlipstogetherul | 0.2742 | 0.2521 | 0.0000 | 0.0221 | 0.2742 | 0.2521 |
| ctrl_expressions_mouthlipspurseur | 0.2771 | 0.1841 | 0.0145 | 0.0930 | 0.2626 | 0.1696 |
| ctrl_expressions_mouthlipstogetherdr | 0.0000 | 0.2521 | 0.0000 | 0.2521 | 0.0000 | 0.2521 |
| ctrl_expressions_mouthlipstogetherdl | 0.0004 | 0.2521 | 0.0000 | 0.2517 | 0.0004 | 0.2521 |
| ctrl_expressions_eyesquintinnerl | 0.2312 | 0.2312 | 0.0000 | 0.0000 | 0.2312 | 0.2312 |
| ctrl_expressions_eyelookrightl | 0.0000 | 0.0000 | 0.2298 | 0.0000 | 0.2298 | 0.2298 |
| ctrl_expressions_browlaterall | 0.0049 | 0.0682 | 0.2304 | 0.0633 | 0.2255 | 0.1621 |
| ctrl_expressions_mouthfunnelul | 0.1655 | 0.3772 | 0.0109 | 0.2117 | 0.1546 | 0.3663 |
| ctrl_expressions_mouthfunnelur | 0.1794 | 0.3772 | 0.0109 | 0.1978 | 0.1685 | 0.3663 |
| ctrl_expressions_browlateralr | 0.0028 | 0.0000 | 0.2004 | 0.0028 | 0.1977 | 0.2004 |
| ctrl_expressions_mouthcornerdepressr | 0.1790 | 0.1790 | 0.0000 | 0.0000 | 0.1790 | 0.1790 |

## Frame 725

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_browlaterall | 0.0069 | 0.0720 | 0.9028 | 0.0651 | 0.8959 | 0.8308 |
| ctrl_expressions_mouthlipstogetherdr | 0.1301 | 0.7322 | 1.0000 | 0.6021 | 0.8699 | 0.2678 |
| ctrl_expressions_mouthlipstogetherdl | 0.1328 | 0.7322 | 1.0000 | 0.5994 | 0.8672 | 0.2678 |
| ctrl_expressions_browlateralr | 0.0055 | 0.0042 | 0.8556 | 0.0014 | 0.8500 | 0.8514 |
| ctrl_expressions_browraiseinr | 1.0000 | 1.0021 | 1.6158 | 0.0021 | 0.6158 | 0.6137 |
| ctrl_expressions_browraiseinl | 1.0000 | 1.0021 | 1.6153 | 0.0021 | 0.6153 | 0.6133 |
| ctrl_expressions_mouthlipstogetherul | 0.4011 | 0.7322 | 1.0000 | 0.3311 | 0.5989 | 0.2678 |
| ctrl_expressions_mouthlipstogetherur | 0.4055 | 0.7322 | 1.0000 | 0.3267 | 0.5945 | 0.2678 |
| ctrl_expressions_eyelookrightl | 0.0000 | 0.0000 | 0.5535 | 0.0000 | 0.5535 | 0.5535 |
| ctrl_expressions_tonguewide | 0.4238 | 0.0964 | 0.0000 | 0.3274 | 0.4237 | 0.0963 |
| ctrl_expressions_eyelookrightr | 0.0000 | 0.0000 | 0.4198 | 0.0000 | 0.4198 | 0.4198 |
| ctrl_expressions_eyewidenl | 0.6306 | 0.6306 | 0.2874 | 0.0000 | 0.3432 | 0.3432 |
| ctrl_expressions_mouthfunneldl | 0.0254 | 0.1821 | 0.3269 | 0.1567 | 0.3015 | 0.1448 |
| ctrl_expressions_mouthfunneldr | 0.0301 | 0.1821 | 0.3269 | 0.1520 | 0.2968 | 0.1448 |
| ctrl_expressions_mouthfunnelul | 0.0330 | 0.1821 | 0.3269 | 0.1491 | 0.2939 | 0.1448 |
| ctrl_expressions_eyewidenr | 0.5808 | 0.5808 | 0.2888 | 0.0000 | 0.2920 | 0.2920 |
| ctrl_expressions_mouthfunnelur | 0.0527 | 0.1821 | 0.3269 | 0.1294 | 0.2742 | 0.1448 |
| ctrl_expressions_mouthcornerdepressl | 0.0912 | 0.0912 | 0.3440 | 0.0000 | 0.2528 | 0.2528 |
| ctrl_expressions_browraiseouterl | 1.0000 | 0.9979 | 0.7598 | 0.0021 | 0.2402 | 0.2382 |
| ctrl_expressions_browraiseouterr | 1.0000 | 0.9979 | 0.7602 | 0.0021 | 0.2398 | 0.2377 |
| ctrl_expressions_eyelookleftl | 0.2193 | 0.2193 | 0.0000 | 0.0000 | 0.2193 | 0.2193 |
| ctrl_expressions_mouthlipspurseul | 0.2809 | 0.2421 | 0.0623 | 0.0387 | 0.2185 | 0.1798 |
| ctrl_expressions_mouthlipstowardsur | 0.2189 | 0.0998 | 0.0257 | 0.1191 | 0.1932 | 0.0741 |
| ctrl_expressions_mouthlipspurseur | 0.2518 | 0.2421 | 0.0623 | 0.0096 | 0.1894 | 0.1798 |
| ctrl_expressions_eyelookleftr | 0.1819 | 0.1819 | 0.0000 | 0.0000 | 0.1819 | 0.1819 |
| ctrl_expressions_jawchinraisedr | 0.1758 | 0.1718 | 0.0000 | 0.0040 | 0.1758 | 0.1718 |
| ctrl_expressions_jawchinraisedl | 0.1678 | 0.1718 | 0.0000 | 0.0040 | 0.1678 | 0.1718 |
| ctrl_expressions_jawopen | 0.2897 | 0.1250 | 0.1845 | 0.1647 | 0.1051 | 0.0595 |
| ctrl_expressions_mouthlowerlipdepressr | 0.0149 | 0.0149 | 0.1686 | 0.0000 | 0.1537 | 0.1537 |
| ctrl_expressions_mouthlowerlipdepressl | 0.0048 | 0.0048 | 0.1434 | 0.0000 | 0.1386 | 0.1386 |

## Frame 956

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_tonguewide | 0.9976 | 0.2269 | 0.0000 | 0.7707 | 0.9976 | 0.2269 |
| ctrl_expressions_browlaterall | 0.0125 | 0.0933 | 0.9141 | 0.0808 | 0.9015 | 0.8207 |
| ctrl_expressions_browlateralr | 0.0150 | 0.0092 | 0.8612 | 0.0058 | 0.8462 | 0.8520 |
| ctrl_expressions_eyesquintinnerr | 1.0000 | 1.0000 | 0.1730 | 0.0000 | 0.8270 | 0.8270 |
| ctrl_expressions_mouthlipstogetherdr | 0.2347 | 1.0000 | 1.0000 | 0.7653 | 0.7653 | 0.0000 |
| ctrl_expressions_mouthlipstogetherdl | 0.2371 | 1.0000 | 1.0000 | 0.7629 | 0.7629 | 0.0000 |
| ctrl_expressions_browraiseinr | 1.0000 | 1.0046 | 1.6298 | 0.0046 | 0.6298 | 0.6253 |
| ctrl_expressions_eyesquintinnerl | 0.8027 | 0.8027 | 0.1749 | 0.0000 | 0.6278 | 0.6278 |
| ctrl_expressions_browraiseinl | 1.0000 | 1.0046 | 1.6267 | 0.0046 | 0.6267 | 0.6221 |
| ctrl_expressions_mouthlipspursedr | 0.5386 | 0.4337 | 0.0000 | 0.1049 | 0.5386 | 0.4337 |
| ctrl_expressions_mouthlipspurseul | 0.5219 | 0.4337 | 0.0000 | 0.0882 | 0.5219 | 0.4337 |
| ctrl_expressions_mouthlipspursedl | 0.5187 | 0.4337 | 0.0000 | 0.0850 | 0.5187 | 0.4337 |
| ctrl_expressions_mouthlipspurseur | 0.4320 | 0.4337 | 0.0000 | 0.0017 | 0.4320 | 0.4337 |
| ctrl_expressions_jawopen | 0.5320 | 0.1549 | 0.1658 | 0.3771 | 0.3662 | 0.0109 |
| ctrl_expressions_mouthfunnelur | 0.0009 | 0.3261 | 0.1379 | 0.3253 | 0.1370 | 0.1883 |
| ctrl_expressions_mouthfunnelul | 0.0017 | 0.3261 | 0.1379 | 0.3244 | 0.1362 | 0.1883 |
| ctrl_expressions_eyelookupl | 0.3147 | 0.3147 | 0.0000 | 0.0000 | 0.3147 | 0.3147 |
| ctrl_expressions_eyelookupr | 0.3066 | 0.3066 | 0.0000 | 0.0000 | 0.3066 | 0.3066 |
| ctrl_expressions_tonguedown | 0.0000 | 0.2984 | 0.0000 | 0.2984 | 0.0000 | 0.2984 |
| ctrl_expressions_eyewidenl | 0.2920 | 0.2920 | 0.0000 | 0.0000 | 0.2920 | 0.2920 |
| ctrl_expressions_tongueout | 0.0000 | 0.2778 | 0.0000 | 0.2778 | 0.0000 | 0.2778 |
| ctrl_expressions_mouthfunneldl | 0.0621 | 0.3261 | 0.1379 | 0.2641 | 0.0758 | 0.1883 |
| ctrl_expressions_mouthlipstogetherul | 0.7368 | 1.0000 | 1.0000 | 0.2632 | 0.2632 | 0.0000 |
| ctrl_expressions_mouthlipstogetherur | 0.7417 | 1.0000 | 1.0000 | 0.2583 | 0.2583 | 0.0000 |
| ctrl_expressions_mouthfunneldr | 0.0687 | 0.3261 | 0.1379 | 0.2575 | 0.0692 | 0.1883 |
| ctrl_expressions_mouthlowerlipdepressr | 0.0037 | 0.0037 | 0.2473 | 0.0000 | 0.2435 | 0.2435 |
| ctrl_expressions_browraiseouterl | 1.0000 | 0.9954 | 0.7655 | 0.0046 | 0.2345 | 0.2299 |
| ctrl_expressions_browraiseouterr | 1.0000 | 0.9954 | 0.7687 | 0.0046 | 0.2313 | 0.2268 |
| ctrl_expressions_mouthlowerlipdepressl | 0.0032 | 0.0032 | 0.2289 | 0.0000 | 0.2258 | 0.2258 |
| ctrl_expressions_eyecheekraiser | 0.2700 | 0.2700 | 0.0678 | 0.0000 | 0.2022 | 0.2022 |

## Frame 1087

| Curve | A | B | C | |A-B| | |A-C| | |B-C| |
|-------|---|---|---|-------|-------|-------|
| ctrl_expressions_mouthfunnelur | 0.0003 | 0.4049 | 1.1786 | 0.4046 | 1.1783 | 0.7737 |
| ctrl_expressions_mouthfunnelul | 0.0011 | 0.4049 | 1.1786 | 0.4037 | 1.1774 | 0.7737 |
| ctrl_expressions_mouthfunneldr | 0.0264 | 0.4049 | 1.1786 | 0.3785 | 1.1522 | 0.7737 |
| ctrl_expressions_mouthfunneldl | 0.0268 | 0.4049 | 1.1786 | 0.3781 | 1.1518 | 0.7737 |
| ctrl_expressions_browlaterall | 0.0068 | 0.0715 | 0.9967 | 0.0647 | 0.9898 | 0.9251 |
| ctrl_expressions_mouthlipstogetherdr | 0.0617 | 1.0000 | 0.7207 | 0.9383 | 0.6590 | 0.2793 |
| ctrl_expressions_mouthlipstogetherdl | 0.0626 | 1.0000 | 0.7207 | 0.9374 | 0.6581 | 0.2793 |
| ctrl_expressions_browlateralr | 0.0098 | 0.0055 | 0.9434 | 0.0042 | 0.9337 | 0.9379 |
| ctrl_expressions_browraiseinr | 1.0000 | 1.0028 | 1.8027 | 0.0028 | 0.8027 | 0.7999 |
| ctrl_expressions_browraiseinl | 1.0000 | 1.0028 | 1.8021 | 0.0028 | 0.8021 | 0.7994 |
| ctrl_expressions_eyeblinkr | 0.7676 | 0.7676 | 0.0000 | 0.0000 | 0.7676 | 0.7676 |
| ctrl_expressions_eyeblinkl | 0.7207 | 0.7207 | 0.0000 | 0.0000 | 0.7207 | 0.7207 |
| ctrl_expressions_mouthlowerlipdepressr | 0.0039 | 0.0039 | 0.7111 | 0.0000 | 0.7072 | 0.7072 |
| ctrl_expressions_mouthlowerlipdepressl | 0.0027 | 0.0027 | 0.7014 | 0.0000 | 0.6987 | 0.6987 |
| ctrl_expressions_eyewidenr | 0.0000 | 0.0000 | 0.6515 | 0.0000 | 0.6515 | 0.6515 |
| ctrl_expressions_eyewidenl | 0.0000 | 0.0000 | 0.6493 | 0.0000 | 0.6493 | 0.6493 |
| ctrl_expressions_jawopen | 0.6150 | 0.1511 | 0.9430 | 0.4639 | 0.3280 | 0.7919 |
| ctrl_expressions_mouthcornerdepressl | 0.1718 | 0.1718 | 0.6126 | 0.0000 | 0.4408 | 0.4408 |
| ctrl_expressions_mouthcornerdepressr | 0.1847 | 0.1847 | 0.6180 | 0.0000 | 0.4333 | 0.4333 |
| ctrl_expressions_mouthupperliprollinr | 0.0200 | 0.0521 | 0.4363 | 0.0321 | 0.4163 | 0.3842 |
| ctrl_expressions_mouthupperliprollinl | 0.0459 | 0.0521 | 0.4363 | 0.0062 | 0.3904 | 0.3842 |
| ctrl_expressions_eyelookrightl | 0.0000 | 0.0000 | 0.3570 | 0.0000 | 0.3570 | 0.3570 |
| ctrl_expressions_eyelookupl | 0.3315 | 0.3315 | 0.0000 | 0.0000 | 0.3315 | 0.3315 |
| ctrl_expressions_mouthlipstogetherul | 0.6787 | 1.0000 | 0.7207 | 0.3213 | 0.0420 | 0.2793 |
| ctrl_expressions_eyelookupr | 0.3208 | 0.3208 | 0.0000 | 0.0000 | 0.3208 | 0.3208 |
| ctrl_expressions_mouthlipstogetherur | 0.6831 | 1.0000 | 0.7207 | 0.3169 | 0.0376 | 0.2793 |
| ctrl_expressions_mouthstretchl | 0.1785 | 0.1785 | 0.4908 | 0.0000 | 0.3123 | 0.3123 |
| ctrl_expressions_eyesquintinnerr | 0.2885 | 0.2885 | 0.0000 | 0.0000 | 0.2885 | 0.2885 |
| ctrl_expressions_mouthstretchr | 0.2289 | 0.2289 | 0.5075 | 0.0000 | 0.2786 | 0.2786 |
| ctrl_expressions_eyelookrightr | 0.0000 | 0.0000 | 0.2595 | 0.0000 | 0.2595 | 0.2595 |
