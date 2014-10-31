install:
install -m 0755 callirhoe $(prefix)/bin
install -m 0755 calmagick $(prefix)/bin
    install -m 644 holidays/ $(prefix)/share/callirhoe
    install -m 644 holidays/germany_berlin_holidays.DE.dat $(prefix)/share/callirhoe
    install -m 644 holidays/greek_holidays.EL.dat $(prefix)/share/callirhoe
    install -m 644 holidays/french_holidays.EN.dat $(prefix)/share/callirhoe
    install -m 644 holidays/french_holidays_zone_A.FR.dat $(prefix)/share/callirhoe
    install -m 644 holidays/french_holidays_zone_C.FR.dat $(prefix)/share/callirhoe
    install -m 644 holidays/generic_holidays.EN.dat $(prefix)/share/callirhoe
    install -m 644 holidays/french_holidays_zone_B.FR.dat $(prefix)/share/callirhoe
    install -m 644 holidays/french_holidays.FR.dat $(prefix)/share/callirhoe
    install -m 644 holidays/greek_namedays.EL.dat $(prefix)/share/callirhoe
