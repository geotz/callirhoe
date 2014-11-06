DESTDIR=/usr/local

all:
	cd scripts && ./make_pkg

install: install-package

install-package:
	mkdir -p $(DESTDIR)/bin
	mkdir -p $(DESTDIR)/share/callirhoe/holidays
	install -m755 callirhoe $(DESTDIR)/bin/callirhoe
	install -m755 calmagick $(DESTDIR)/bin/calmagick
	install -m644 holidays/* $(DESTDIR)/share/callirhoe/holidays/

clean:
	rm -f callirhoe calmagick
