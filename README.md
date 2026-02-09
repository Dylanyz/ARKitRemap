# ARKitRemap
remap metahuman animator curves to arkit curves to drive morph targets.
rig any character with 'faceit' and get MHA quality. No need for iphones, use any monocular camera.

it's done through an 'animation modifier' to convert your animation sequences.

-------
# Instructions
1. Drag the .uasset into your content folder of your project.
2. Process your metahuman performance and export as animation sequence - select your custom character as the skeleton in the export dialog. If you already have an animation sequence - duplicate it if you want to preserve the original, and see the *note* below.
3. Right click the sequence -> add modifiers -> AM_ArKitRemap
4. Your animation asset now contains ArKit compatible curves. You can add to the character animation track in sequencer by clicking the + on the animation track.

*(note) If you didn't select the custom character on exporting your animation sequence, you can still add in sequencer: click + on the character's animation track, then 'allow incompatible skeletons' and add the animation. Or you can retarget the animation and it will appear by default.*

ALL NODES:
<img width="1822" height="735" alt="Screenshot 2026-02-08 211816" src="https://github.com/user-attachments/assets/bb578f81-1745-4f6b-953f-901fde352924" />
MAIN SERIES:
<img width="1481" height="221" alt="Screenshot 2026-02-07 135951" src="https://github.com/user-attachments/assets/ff1ba2c2-30fb-4fb6-9656-1cae7edccec6" />
JAW / MOUTH:
<img width="2086" height="639" alt="Screenshot 2026-02-08 211822" src="https://github.com/user-attachments/assets/b9663672-9c0c-46c6-b0e8-0e1ee327aaae" />

# Jaw + Mouth calculations
You can play with the Max clamp value for this calculation if your mouth is deformed, or just delete the MouthOpen curve entirely.
This modifier asset is attempting to reverse engineer the blueprint ABP_MH_LiveLink located in Content/MetaHumans/Common/Animation
This blueprint is a really good reference because it shows how Epic converts ARKit into Metahuman curves.

# Getting it to work with body animations
I recommend a *slot system* for this.
1. Make an animation blueprint for your character.
2. In bottom right - Anim Slot Manager. Add slot. Call it FaceSlot.
3. Add a Layered Blend Per Bone node.
Connect the body slot → Base Pose input.
Connect the face slot → Blend Poses 0 input.
5.  Configure the Layered Blend Per Bone Node.
Select the Layered Blend Per Bone node and in the Details panel:
Blend Mode: You have two options here:

Branch Filter (default) — In the Layer Setup section, click + to add an entry. Set Bone Name to head (or whatever the head bone is called on your skeleton). Set Blend Depth to 1. This tells UE: "the face animation only affects the head bone and its children."
6. Assign animation slot in sequencer. Right click your section of the animation in sequencer- go to animation - slot, and type your slot name.

Basically this will make the face animation only affect above the head bone, and body is everything else, so they dont interfere.

# Videos:
Arkit vs MHA translated to Arkit comparison (this is before i did the mouth fix)
https://youtu.be/oiIFQVm8Pug

This video explains what's going on with this asset. Instead of renaming the curves in the animation sequence, I made an asset to do it automatically to ANY sequence. https://youtu.be/EF0tNFFY00Y?si=K5xUtGHVuF-Ryord
