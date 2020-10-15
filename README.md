# FileOptimizerPy
---
Python module and utility for file compression with several optimization plugins.

Based on utility [FileOptimiser](https://nikkhokkho.sourceforge.io/static.php?page=FileOptimizer) by Nikkho.

License: **AGPLv3**
Version: **1.0.1580**
Python version: **>=3.6**

Required plugins from original utility: 
`ImageMagick, ImageWorsener, CSSTidy, PETrim, strip, UPX, Leanify, shntool, FLAC, FLACOut, gifsicle, flexiGIF, Libdeflate, ECT, advdef, zRecompress, DeflOpt, defluff, tidy-html5, Guetzli, jpeg-recompress, jhead, jpegoptim, jpegtran, mozjpegtran, pingo, JSMin, ffmpeg, mkclean, advmng, MP3packer, mp4v2, rehuff, rehuff_theora, Document Press, Best CFBF, mutool, ghostcript, cpdfsqueeze, apngopt, pngquant, PngOptimizer, TruePNG, PNGOut, OptiPNG, pngwolf, pngrewrite, advpng, flasm, sqlite, dwebp, cwebp, advzip, m7zRepacker`

## How to install

    $ pip3 install FileOptimizerPy
 
## Checking documentation

    $ pydoc3 FileOptimizer

## Examples of usage

```python
from FileOptimizer import FileOptimiser

f = FileOptimiser()
f.getFiles('C:\\Images')
f.filter(lambda x: x.suffix != '.png')
f.sort(lambda x: x.stat().st_size, reverse=True)
f.sort(lambda x: x.suffix)
result = f.optimise(silentMode=False, processes=4)
total_optimisation = sum(i['Original'] for i in result) / sum(i['Optimized'] for i in result)
```

```
$ python3 -m FileOptimizer -s "C:\Images"
```