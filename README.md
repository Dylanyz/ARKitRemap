# ARKitRemap
remap metahuman animator curves to arkit curves to drive morph targets.
rig any character with 'faceit' and get MHA quality. No need for iphones, use any monocular camera.

it's done through an 'animation modifier' to convert your animation sequences.

-------

1. Drag the .uasset into your content folder of your project.
2. Process your metahuman performance and export as animation sequence - select your custom character as the skeleton in the export dialog. If you already have an animation sequence - duplicate it if you want to preserve the original, and see the *note* below.
3. Right click the sequence -> add modifiers -> AM_ArKitRemap
4. Your animation asset now contains ArKit compatible curves. You can add to the character animation track in sequencer by clicking the + on the animation track.


(note) If you didn't select the custom character on exporting your animation sequence, you can still add in sequencer: click + on the character's animation track, then 'allow incompatible skeletons' and add the animation. Or you can retarget the animation and it will appear by default.

<img width="1481" height="221" alt="Screenshot 2026-02-07 135951" src="https://github.com/user-attachments/assets/ff1ba2c2-30fb-4fb6-9656-1cae7edccec6" />

Comparison video:
https://youtu.be/oiIFQVm8Pug

This video explains what's going on. Instead of renaming the curves in the animation sequence, I made an asset to do it automatically to ANY sequence. https://youtu.be/EF0tNFFY00Y?si=K5xUtGHVuF-Ryord
