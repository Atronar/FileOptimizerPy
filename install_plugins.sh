sudo apt install wine-stable

sudo apt install advancecomp
sudo apt install apngopt

sudo apt install ocaml libcamlpdf-ocaml-dev &&
git clone https://github.com/johnwhitington/cpdfsqueeze.git &&
cd cpdfsqueeze &&
make &&
mv cpdfsqueeze ~/FOPlugins/cpdfsqueeze &&
cd .. &&
rm -r cpdfsqueeze

git clone https://github.com/csstidy-c/csstidy.git &&
cd csstidy &&
make &&
sudo make install &&
cd .. &&
rm -r csstidy

sudo apt install webp

sudo apt install p7zip-full &&
wget https://github.com/imgo/imgo-tools/raw/master/src/defluff/defluff-0.3.2-linux-`uname -m`.zip -O defluff.zip &&
7z x defluff.zip &&
chmod a+x defluff &&
mv defluff ~/FOPlugins/defluff

sudo apt install nasm &&
wget https://github.com/Kitware/CMake/releases/download/v3.18.4/cmake-3.18.4-Linux-x86_64.sh &&
chmod a+x cmake-3.18.4-Linux-x86_64.sh &&
./cmake-3.18.4-Linux-x86_64.sh &&
rm cmake-3.18.4-Linux-x86_64.sh &&
cp -aT cmake-3.18.4-Linux-x86_64/ /usr/local/

git clone --recursive https://github.com/fhanau/Efficient-Compression-Tool.git &&
cd Efficient-Compression-Tool &&
mkdir build &&
cd build &&
cmake ../db_src &&
make &&
mv ect ~/FOPlugins/ECT &&
cd ../.. &&
rm -r Efficient-Compression-Tool

sudo apt install ffmpeg
sudo apt install flac
sudo apt install flasm

wget https://create.stephan-brumme.com/flexigif-lossless-gif-lzw-optimization/flexiGIF.2018.11a &&
chmod a+x flexiGIF.2018.11a &&
mv flexiGIF.2018.11a ~/FOPlugins/flexiGIF

sudo apt install gifsicle
sudo apt install ghostscript
sudo apt install guetzli

sudo apt install autoconf automake libtool libpng-dev libjpeg-dev libwebp-dev &&
git clone https://github.com/jsummers/imageworsener.git &&
cd imageworsener &&
scripts/autogen.sh &&
./configure &&
make -C scripts &&
make install &&
cd .. &&
rm -r imageworsener

sudo apt install jhead
sudo apt install jpegoptim

git clone https://github.com/mozilla/mozjpeg.git &&
cd mozjpeg &&
mkdir build && cd build &&
cmake -G"Unix Makefiles" --with-jpeg8 ../ &&
make &&
sudo make install &&
sudo ln -s /opt/mozjpeg/bin/cjpeg /usr/bin/mozjpeg &&
sudo ln -s /opt/mozjpeg/bin/jpegtran /usr/bin/mozjpegtran &&
cp /opt/mozjpeg/bin/jpegtran ~/FOPlugins/mozjpegtran &&
git clone https://github.com/danielgtaylor/jpeg-archive.git &&
cd jpeg-archive/ &&
make &&
sudo make install &&
cd .. &&
rm -r mozjpeg jpeg-archive

sudo apt install libjpeg-progs

git clone https://github.com/JayXon/Leanify.git &&
cd Leanify &&
make &&
mv leanify ~/FOPlugins/Leanify &&
cd .. &&
rm -r Leanify

sudo apt install gzip
sudo apt install imagemagick

sudo apt install tofrodos &&
git clone https://github.com/kepstin/mkclean.git &&
cd mkclean &&
fromdos mkclean/configure.compiled &&
./mkclean/configure.compiled &&
make -C mkclean install &&
cd .. &&
rm -r mkclean

git clone https://github.com/hmage/mp3packer &&
cd mp3packer &&
make &&
mv mp3packer ~/FOPlugins/mp3packer &&
cd .. &&
rm -r mp3packer

sudo apt install mp4v2-utils
sudo apt install mupdf-tools
sudo apt install optipng

sudo add-apt-repository ppa:psydk/pngoptimizer &&
sudo apt update &&
sudo apt install pngoptimizer

wget http://www.jonof.id.au/files/kenutils/pngout-20200115-linux.tar.gz &&
tar -xf pngout-20200115-linux.tar.gz &&
rm pngout-20200115-linux.tar.gz &&
cp pngout-20200115-linux/$(dpkg --print-architecture)/pngout /usr/bin/pngout &&
cp pngout-20200115-linux/$(dpkg --print-architecture)/pngout ~/FOPlugins/pngout &&
rm -r pngout-20200115-linux

sudo apt install pngquant

wget http://entropymine.com/jason/pngrewrite/pngrewrite-1.4.0.zip &&
7z x pngrewrite-1.4.0.zip -opngrewrite &&
rm pngrewrite-1.4.0.zip &&
cd pngrewrite &&
make &&
mv pngrewrite ~/FOPlugins/pngrewrite &&
cd .. &&
rm -r pngrewrite

git clone --recursive https://github.com/jibsen/pngwolf-zopfli.git &&
cd pngwolf-zopfli &&
cmake CMakeLists.txt &&
makedirs &&
mv pngwolf ~/FOPlugins/pngwolf &&
cd .. &&
rm -r pngwolf-zopfli

sudo apt install libogg-dev &&
git clone https://github.com/uyjulian/rehuff.git &&
cd rehuff &&
make &&
mv rehuff ~/FOPlugins/rehuff &&
cd .. &&
rm -r rehuff

sudo apt install libvorbis-dev subversion &&
svn co http://svn.xiph.org/trunk/theora-exp &&
cd theora-exp &&
./autogen.sh &&
cd unix &&
make rehuff &&
mv rehuff ~/FOPlugins/rehuff_theora &&
cd ../.. &&
rm -r theora-exp

sudo apt install shntool
sudo apt install sqlite3
sudo ln -s /usr/bin/strip ~/FOPlugins/strip
sudo apt install tidy
sudo apt install upx-ucl
