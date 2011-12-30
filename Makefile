all:
	mkdir -p ./local/lib
	cp /usr/lib/libblas* ./local/lib
	cp /usr/lib/lapack/* ./local/lib
	cp /usr/lib/libxerces* ./local/lib
	cp /usr/lib/libarpack* ./local/lib
	cp /usr/lib/libumfpack* ./local/lib
	./femhub -b

clean:
	rm -rf spkg/build

distclean: clean
	rm -rf local
	rm -rf spkg/installed/*
