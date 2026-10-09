# `ColorsShare/algorithm`
The inner algorithm that makes ColorsShare possible

## History
Back in early 2024 I had an idea : what if you could "compress" any file using QR Codes ?  
But QR Codes have only 2 "states", white or black, 0 or 1. What if instead we used all the color spectrum ? That's 16 777 216 different combinations in RGB (1 677 721 600 if you add the alpha channel), which means every pixel on the image would be able to represent 3.75 bytes/30 bits (`1100011111111111111111111111111`/`0x63FFFFFF`).

$$\lfloor\log_2(1\\,677\\,721\\,600)\rfloor=30$$

Now that surely makes the QR code impossible to scan, but what if we don't ? We could simply put that in an image and send it, the end user just downloads said image and decompresses it ! Furthermore, we could drop some of the QR code's properties (alignment, error correction duplication, ...) to have even more data in the image, which would just look like pixel soup (+ some markers in the corners to remove orientation issues).  
At the time GPT 4 Turbo was SOTA (could you believe it ??) so I made it make an early version of the algorithm (which you can find in [`clsh.py`](./clsh.py)), which seemed to work on text files (although some parts were missing) and any binary file would be unreadable. But I was sorta hyped, especially as files sizes were basically halved. That's an insane compression ratio dude ! I already seen myself running the algo multiple times (with a way to keep track of generations) so it gets smaller, in the end creating a pixel matrix that's simple colors (like GIFs) & easily shareable.  
Now there's [obviously](https://en.wikipedia.org/wiki/Entropy_(information_theory)) a [catch](https://en.wikipedia.org/wiki/Shannon%27s_source_coding_theorem), but I wasn't realistic enough to see it.  
Fast forward a year and the SOTA is now GPT-5 Pro, which I used as I thought again about this project to fix the issues of the previous code. And... well it shattered my expectations, as the files produced are just exactly, if not slightly bigger, the same size. So... [`clsh2.py`](./clsh2.py) could just be used to "obfuscate" the data ?  
It's now been another year and there's no reason to keep it private anymore. The GH org has been deleted long since, and every other planned sub-project (CLI, desktop & mobile apps, ...) has been dropped. It's just a silly idea at the end of the day 😝
