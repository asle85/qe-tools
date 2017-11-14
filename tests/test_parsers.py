#!/usr/bin/env python
from __future__ import print_function
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, open,
         pow, round, super,
         filter, map, zip)


import os
import unittest
import json

from qe_tools import PwInputFile, CpInputFile

# Folder with input file examples
data_folder = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')
# Folder with parsing comparison
reference_folder = os.path.join(data_folder, 'ref')

class CustomTestCase(unittest.TestCase):
    """
    Extension of the unittest TestCase to support also deep almost-equal
    comparisons of dicts 
    )
    """

    def assertNestedAlmostEqual(self, expected, actual, *args, **kwargs):
        """
        Check that dict have almost equal content, for float content.
        Works recursively for dicts, tuples, lists, ... Use
        :py:meth:`unittest.TestCase.assertEqual` except for numbers, where
        :py:meth:`unittest.TestCase.assertAlmostEqual` is used.
        Additional parameters are passed only to AlmostEqual
        """
        import numpy
        is_root = not '__trace' in kwargs
        trace = kwargs.pop('__trace', 'ROOT')
        try:
            if isinstance(expected, (int, float, complex)):
                self.assertAlmostEqual(expected, actual, *args, **kwargs)
            elif isinstance(expected, (list, tuple, numpy.ndarray)):
                self.assertEqual(len(expected), len(actual))
                for index in range(len(expected)):
                    v1, v2 = expected[index], actual[index]
                    self.assertNestedAlmostEqual(v1, v2,
                                          __trace=repr(index), *args, **kwargs)
            elif isinstance(expected, dict):
                self.assertEqual(set(expected), set(actual))
                for key in expected:
                    self.assertNestedAlmostEqual(expected[key], actual[key],
                                        __trace=repr(key), *args, **kwargs)
            else:
                self.assertEqual(expected, actual)
        except AssertionError as exc:
            exc.__dict__.setdefault('traces', []).append(trace)
            if is_root:
                trace = ' -> '.join(reversed(exc.traces))
                exc = AssertionError("%s\nTRACE: %s" % (str(exc), trace))
            raise exc

    def assertNestedAlmostEqualOnlyKeysInFirst(self, expected, actual, *args, **kwargs):
        """
        Check that dict have almost equal content, for float content.

        Check only keys in first dictionary (i.e. if it contains less keys,
        only those are checked). 
        Works recursively for dicts, tuples, lists, ... Use
        :py:meth:`unittest.TestCase.assertEqual` except for numbers, where
        :py:meth:`unittest.TestCase.assertAlmostEqual` is used.
        Additional parameters are passed only to AlmostEqual
        """
        import numpy
        is_root = not '__trace' in kwargs
        trace = kwargs.pop('__trace', 'ROOT')
        try:
            if isinstance(expected, (int, float, complex)):
                self.assertAlmostEqual(expected, actual, *args, **kwargs)
            elif isinstance(expected, (list, tuple, numpy.ndarray)):
                self.assertEqual(len(expected), len(actual))
                for index in range(len(expected)):
                    v1, v2 = expected[index], actual[index]
                    self.assertNestedAlmostEqual(v1, v2,
                                          __trace=repr(index), *args, **kwargs)
            elif isinstance(expected, dict):
                self.assertEqual(set(expected), set(actual).intersection(set(expected)))
                for key in expected:
                    self.assertNestedAlmostEqualOnlyKeysInFirst(expected[key], actual[key],
                                        __trace=repr(key), *args, **kwargs)
            else:
                self.assertEqual(expected, actual)
        except AssertionError as exc:
            exc.__dict__.setdefault('traces', []).append(trace)
            if is_root:
                trace = ' -> '.join(reversed(exc.traces))
                exc = AssertionError("%s\nTRACE: %s" % (str(exc), trace))
            raise exc


class PwTest(CustomTestCase):
    def singletest(self, label, parser='pw'):
        """
        Run a single test.

        :param label: used to generate the filename (<label>.in)
        :param parser: used to define the parser to use. Possible values: 
            ``pw``, ``cp``.
        """        
        fname = os.path.join(data_folder, '{}.in'.format(label))
        if not os.path.isfile(fname):
            raise ValueError("File {} not found".format(fname))
        if parser == 'pw':
            ParserClass = PwInputFile
        elif parser == 'cp':
            ParserClass = CpInputFile
        else:
            raise ValueError("Invalid valude for 'parser': '{}'".format(parser))

        in_fname = ParserClass(fname)

        # Check opening as file-object
        with open(fname) as f:
            in_fobj = ParserClass(f)
        self.assertNestedAlmostEqual(in_fname.atomic_positions, in_fobj.atomic_positions)
        self.assertNestedAlmostEqual(in_fname.atomic_species, in_fobj.atomic_species)
        self.assertNestedAlmostEqual(in_fname.cell_parameters, in_fobj.cell_parameters)
        self.assertNestedAlmostEqual(in_fname.k_points, in_fobj.k_points)
        self.assertNestedAlmostEqual(in_fname.namelists, in_fobj.namelists)

        # Check opening from string with file content
        with open(fname) as f:
            content = f.read()
            in_string = ParserClass(content)
        self.assertNestedAlmostEqual(in_string.atomic_positions, in_fobj.atomic_positions)
        self.assertNestedAlmostEqual(in_string.atomic_species, in_fobj.atomic_species)
        self.assertNestedAlmostEqual(in_string.cell_parameters, in_fobj.cell_parameters)
        self.assertNestedAlmostEqual(in_string.k_points, in_fobj.k_points)
        self.assertNestedAlmostEqual(in_string.namelists, in_fobj.namelists)

        result = {
            "atomic_positions": in_fname.atomic_positions,
            "atomic_species": in_fname.atomic_species,
            "cell_parameters": in_fname.cell_parameters,
            "namelists": in_fname.namelists,
        }
        if parser != 'cp':
            result["k_points"] = in_fname.k_points

        ref_fname = os.path.join(reference_folder, '{}.json'.format(label))
        try:
            with open(ref_fname) as f:
                ref = json.load(f)
        except Exception:
            print("What I parsed (to be used in a test reference):")
            print_test_comparison(label=label, parser=parser, write=False)
            raise

        # Check only things in the first dictionary (that therefore must be the
        # test json). In this way I can remove things from the test json
        # if I don't want to test them.
        self.assertNestedAlmostEqualOnlyKeysInFirst(ref, result)

    ## Here start the tests
    def test_example_ibrav0(self):
        self.singletest(label='example_ibrav0')

    # def test_lattice_ibrav0_cell_parameters(self):
    #     self.singletest(label='lattice_ibrav0_cell_parameters')

    # def test_lattice_ibrav0_cell_parameters_a(self):
    #     self.singletest(label='lattice_ibrav0_cell_parameters_a')

    # def test_lattice_ibrav0_cell_parameters_ang(self):
    #     self.singletest(label='lattice_ibrav0_cell_parameters_ang')

    # def test_lattice_ibrav0_cell_parameters_celldm(self):
    #     self.singletest(label='lattice_ibrav0_cell_parameters_celldm')

    # def test_lattice_ibrav1(self):
    #     self.singletest(label='lattice_ibrav1')

    # def test_lattice_ibrav10(self):
    #     self.singletest(label='lattice_ibrav10')

    # def test_lattice_ibrav10_kauto(self):
    #     self.singletest(label='lattice_ibrav10_kauto')

    # def test_lattice_ibrav11(self):
    #     self.singletest(label='lattice_ibrav11')

    # def test_lattice_ibrav11_kauto(self):
    #     self.singletest(label='lattice_ibrav11_kauto')

    # def test_lattice_ibrav12(self):
    #     self.singletest(label='lattice_ibrav12')

    # def test_lattice_ibrav12_kauto(self):
    #     self.singletest(label='lattice_ibrav12_kauto')

    # def test_lattice_ibrav13(self):
    #     self.singletest(label='lattice_ibrav13')

    # def test_lattice_ibrav13_kauto(self):
    #     self.singletest(label='lattice_ibrav13_kauto')

    # def test_lattice_ibrav14(self):
    #     self.singletest(label='lattice_ibrav14')

    # def test_lattice_ibrav14_kauto(self):
    #     self.singletest(label='lattice_ibrav14_kauto')

    # def test_lattice_ibrav1_kauto(self):
    #     self.singletest(label='lattice_ibrav1_kauto')

    # def test_lattice_ibrav2(self):
    #     self.singletest(label='lattice_ibrav2')

    # def test_lattice_ibrav2_kauto(self):
    #     self.singletest(label='lattice_ibrav2_kauto')

    # def test_lattice_ibrav3(self):
    #     self.singletest(label='lattice_ibrav3')

    # def test_lattice_ibrav3_kauto(self):
    #     self.singletest(label='lattice_ibrav3_kauto')

    # def test_lattice_ibrav4(self):
    #     self.singletest(label='lattice_ibrav4')

    # def test_lattice_ibrav4_kauto(self):
    #     self.singletest(label='lattice_ibrav4_kauto')

    # def test_lattice_ibrav5(self):
    #     self.singletest(label='lattice_ibrav5')

    # def test_lattice_ibrav5_kauto(self):
    #     self.singletest(label='lattice_ibrav5_kauto')

    # def test_lattice_ibrav6(self):
    #     self.singletest(label='lattice_ibrav6')

    # def test_lattice_ibrav6_kauto(self):
    #     self.singletest(label='lattice_ibrav6_kauto')

    # def test_lattice_ibrav7(self):
    #     self.singletest(label='lattice_ibrav7')

    # def test_lattice_ibrav7_kauto(self):
    #     self.singletest(label='lattice_ibrav7_kauto')

    # def test_lattice_ibrav8(self):
    #     self.singletest(label='lattice_ibrav8')

    # def test_lattice_ibrav8_kauto(self):
    #     self.singletest(label='lattice_ibrav8_kauto')

    # def test_lattice_ibrav9(self):
    #     self.singletest(label='lattice_ibrav9')

    # def test_lattice_ibrav9_kauto(self):
    #     self.singletest(label='lattice_ibrav9_kauto')

    # def test_lattice_ibrav_12(self):
    #     self.singletest(label='lattice_ibrav_12')

    # def test_lattice_ibrav_12_kauto(self):
    #     self.singletest(label='lattice_ibrav_12_kauto')

    # def test_lattice_ibrav_3(self):
    #     self.singletest(label='lattice_ibrav_3')

    # def test_lattice_ibrav_3_kauto(self):
    #     self.singletest(label='lattice_ibrav_3_kauto')

    # def test_lattice_ibrav_5(self):
    #     self.singletest(label='lattice_ibrav_5')

    # def test_lattice_ibrav_5_kauto(self):
    #     self.singletest(label='lattice_ibrav_5_kauto')

    # Wyckoff position input (crystal_sg) not supported by this parser
    #def test_lattice_wyckoff_sio2(self):
    #    self.singletest(label='lattice_wyckoff_sio2')


def print_test_comparison(label, parser='pw', write=False):
    """
    Prepare the json to compare the parsing results.

    :param label: used to generate the filename (<label>.in)
    :param parser: used to define the parser to use. Possible values: 
        ``pw``, ``cp``.
    """
    fname = os.path.join(data_folder, '{}.in'.format(label))
    if not os.path.isfile(fname):
        raise ValueError("File {} not found".format(fname))
    if parser == 'pw':
        ParserClass = PwInputFile
    elif parser == 'cp':
        ParserClass = CpInputFile
    else:
        raise ValueError("Invalid valude for 'parser': '{}'".format(parser))

    parsed = ParserClass(fname)

    result = {
        "atomic_positions": parsed.atomic_positions,
        "atomic_species": parsed.atomic_species,
        "cell_parameters": parsed.cell_parameters,
        "namelists": parsed.namelists,
    }
    if parser != 'cp':
        result["k_points"] = parsed.k_points

    if write:
        ref_fname = os.path.join(reference_folder, '{}.json'.format(label))
        with open(ref_fname, 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)
            print("File '{}' written.".format(ref_fname))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))




if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--write-ref':
            try:
                label = sys.argv[2]
            except IndexError:
                print("Pass as filename (and optionally pw or cp to specify a parser, default: pw)", file=sys.stderr)
                sys.exit(1)
            try:
                parser = sys.argv[3]
            except IndexError:
                parser = 'pw'
            print_test_comparison(label, parser=parser, write=True)
        else:
            print("If you pass additional parameters, they must be --write-ref <label> [pw/cp]", file=sys.stderr)

    else:
        unittest.main()


