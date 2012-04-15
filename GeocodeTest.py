from Geocode import PoolNode, SearchPool, SearchSlice, post_process_result
from pyavltree import AVLTree
import re

"""
Test data.

                                      SearchSlice()
                                              |
                --------------------------------------------------------------
                |                                                            |
            SearchSlice(USA)                                         SearchSlice(INDIA)
                |                                                            |
        -----------------------------                               SearchPool(WEST BEANGAL)
        |                           |                                    |
     SearchPool(NEW YORK)        SearchPool(CALIFORNIA)                  |- KOLKATA
        |                           |                                    |- BARA BAZAR, KOLKATA
        |- PEARL STREET             |- PEARL STREET                      |- 101 C, BARA BAZAR, KOLKATA
        |- TIME SQUARE
        |- 101 C, PEARL STREET
        |- 101 C, TIME SQUARE

"""


ny = AVLTree()
ny.insert_node(PoolNode('PEARL STREET'))
ny.insert_node(PoolNode('TIME SQUARE'))
ny.insert_node(PoolNode('101 C', ['PEARL STREET']))
ny.insert_node(PoolNode('101 C', ['TIME SQUARE']))
print ny.out()

poolNY = SearchPool(ny, PoolNode('NEW YORK'))

cali = AVLTree()
cali.insert_node(PoolNode('PEARL STREET'))
print cali.out()

poolCali = SearchPool(cali, PoolNode('CALIFORNIA'))

usa = {
	'NEW YORK': poolNY,
	'CALIFORNIA': poolCali,
}

sliceUSA = SearchSlice(usa, PoolNode('USA'))

wb = AVLTree()
wb.insert_node(PoolNode('KOLKATA'))
wb.insert_node(PoolNode('BARA BAZAR', ['KOLKATA']))
wb.insert_node(PoolNode('101 C', ['KOLKATA', 'BARA BAZAR']))
print wb.out()

poolWB = SearchPool(wb, PoolNode('WEST BENGAL'))

india = {
	'WEST BENGAL': poolWB,
}

sliceIndia = SearchSlice(india, PoolNode('INDIA'))

countries = {
	'USA': sliceUSA,
	'INDIA': sliceIndia,
}

countriesSlice = SearchSlice(countries, PoolNode(''))


def query(q, return_empty=False, limit=-1, max_rank=None):
	# Preprocessing to clean the query string
	q = q.strip()
	q = re.sub(r'\s(\s)+', ' ', q) # Removing multiple spaces
	q = re.sub(r'^,|,$','', q) # Removing extraneous commas
	q = re.sub(r'\s*,\s*',',', q) # Removing spaces around commas
	q = q.upper()

	print 'Query is: ' + q

	# Now query
	q = q.split(',')
	q.reverse()

	return post_process_result( \
		countriesSlice.locate(q, return_empty, limit), \
		q, \
		max_rank)

def print_arr(l):
	s = ''
	for i in l:
		s = s + str(i)+ ', '
	print '[' + s + ']'


print_arr(query('New York, USA'))
print

print_arr(query('New York'))
print

print_arr(query('Pearl Street, New York, USA'))
print

print_arr(query('Pearl Street, USA'))
print

print_arr(query('Pearl Street'))
print

print 'With return_empty=True'
print_arr(query('103 Alkazam, New York, USA', True))
print 'With return_empty=False'
print_arr(query('103 Alkazam, New York, USA', False))
print

print_arr(query('Pearl Street, USA'))
print

print 'With no max_rank'
print_arr(query('101 C, Alley A, Pearl Street, New York'))
print 'With max_rank=70'
print_arr(query('101 C, Alley A, Pearl Street, New York', max_rank=70))
print

print_arr(query('101 C, Alley A, Pearl Street, New York, USA'))
print

print_arr(query('101 C, Alley A, Pearl Street, '))
print

print_arr(query('101 C, New York '))
print

print_arr(query('101 C, Alley A, New York '))
print

print 'With no limit'
print_arr(query('101 C'))
print 'With limit=2'
print_arr(query('101 C', limit=2))
print
