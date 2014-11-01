#!/usr/bin/env python2.7
import glob

res = dict()

for x in ['lang', 'style', 'layouts', 'geom']:
    res[x] = glob.glob('%s/*.py' % x)

print 'resource_list = {}'
for x in res.keys():
    print 'resource_list["%s"] = %s' % (x, str(res[x]))
