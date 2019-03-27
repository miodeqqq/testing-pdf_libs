#! /usr/bin/env python

# -*- coding: utf-8 -*-

import math
import os
import re
import time
import ujson as json
import unicodedata
import warnings
from shutil import rmtree

import plotly.graph_objs as go
import plotly.offline as opy
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from pdfminer.pdfdocument import PDFEncryptionError, PDFDocument
from pdfminer.pdfparser import PDFSyntaxError, PDFParser
from pdfminer.pdftypes import resolve1
from pdfquery import PDFQuery
from pdfrw import PdfReader
from tika import parser

warnings.simplefilter('ignore')


class Colors:
    """
    Class defines colors to be used in console prints.
    """

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CYAN = "\033[1;36m"


class StatisticPlot:
    def __init__(self, regex, pypdf2, pdfrw, pdfquery, tika, pdfminer):
        self.regex = self._read(regex)
        self.pypdf2 = self._read(pypdf2)
        self.pdfrw = self._read(pdfrw)
        self.pdfquery = self._read(pdfquery)
        self.tika = self._read(tika)
        self.pdfminer = self._read(pdfminer)

    def _read(self, file_obj):
        """
        General method to return data done with given tool.
        """

        with open(file_obj, 'r') as data_file:
            return dict([x.lower().strip().split(';') for x in data_file])

    def _make_layout(self):
        """
        Creates final layout with labels for XY axis.
        """

        return go.Layout(
            title='Python libraries performance with reading PDF and gathering info about the number of pages',
            xaxis=dict(
                title='filename',
                autorange=True,
                titlefont=dict(
                    family='Verdana',
                    size=18,
                    color='#7f7f7f'
                )
            ),
            yaxis=dict(
                autorange=True,
                title='processing time (seconds)',
                titlefont=dict(
                    family='Verdana',
                    size=18,
                    color='#7f7f7f'
                )
            ),
        )

    def generate_bar_plot(self):
        """
        General method to generate Bar plot.
        """

        # make Bar plots
        regex_data = go.Bar(
            x=list(self.regex.keys()),
            y=list(self.regex.values()),
            name='REGEX',
        )

        pypdf2_data = go.Bar(
            x=list(self.pypdf2.keys()),
            y=list(self.pypdf2.values()),
            name='PYPDF2',
        )

        pdfrw_data = go.Bar(
            x=list(self.pdfrw.keys()),
            y=list(self.pdfrw.values()),
            name='PDFRW',
        )

        pdfquery_data = go.Bar(
            x=list(self.pdfquery.keys()),
            y=list(self.pdfquery.values()),
            name='PDFQUERY',
        )

        tika_data = go.Bar(
            x=list(self.tika.keys()),
            y=list(self.tika.values()),
            name='TIKA',
        )

        pdfminer_data = go.Bar(
            x=list(self.pdfminer.keys()),
            y=list(self.pdfminer.values()),
            name='PDFMINER',
        )

        data = [
            regex_data,
            pypdf2_data,
            pdfrw_data,
            pdfquery_data,
            tika_data,
            pdfminer_data
        ]

        layout = self._make_layout()

        fig = go.Figure(
            data=data,
            layout=layout
        )

        opy.plot(
            fig,
            filename='./plots/pdfs_performance_bar.html'
        )

    def generate_scatter_plot(self):
        """
        General method to generate Scatter plot.
        """

        # make Scatter plots
        regex_data = go.Scatter(
            x=list(self.regex.keys()),
            y=list(self.regex.values()),
            name='REGEX',
            line=dict(
                color=('rgb(205, 12, 24)'),
                width=4
            )
        )

        pypdf2_data = go.Scatter(
            x=list(self.pypdf2.keys()),
            y=list(self.pypdf2.values()),
            name='PYPDF2',
            line=dict(
                color=('rgb(22, 96, 167)'),
                width=4
            )
        )

        pdfrw_data = go.Scatter(
            x=list(self.pdfrw.keys()),
            y=list(self.pdfrw.values()),
            name='PDFRW',
            line=dict(
                color=('rgb(102, 204, 0)'),
                width=4,
            )
        )

        pdfquery_data = go.Scatter(
            x=list(self.pdfquery.keys()),
            y=list(self.pdfquery.values()),
            name='PDFQUERY',
            line=dict(
                color=('rgb(178, 102, 255)'),
                width=4,
            )
        )

        tika_data = go.Scatter(
            x=list(self.tika.keys()),
            y=list(self.tika.values()),
            name='TIKA',
            line=dict(
                color=('rgb(255, 255, 0)'),
                width=4,
            )
        )

        pdfminer_data = go.Scatter(
            x=list(self.pdfminer.keys()),
            y=list(self.pdfminer.values()),
            name='PDFMINER',
            line=dict(
                color=('rgb(204, 0, 102)'),
                width=4,
            )
        )

        data = [
            regex_data,
            pypdf2_data,
            pdfrw_data,
            pdfquery_data,
            tika_data,
            pdfminer_data
        ]

        layout = self._make_layout()

        fig = go.Figure(
            data=data,
            layout=layout
        )

        opy.plot(
            fig,
            filename='./plots/pdfs_performance_scatter.html'
        )


class LibrariesTesting:
    def __init__(self, path):
        self.path = path
        self.pdfs = self._prepare_pdfs()
        self.pdfs_processing_dir = './pdfs_processing_time'
        self.json_path = './processing_stats'
        self.plots_path = './plots'
        self.default_time = '{:0.5f}'.format(0)
        self.final_stats_dict = {}
        self.single_file_stats = {}
        self.tika_url = 'http://localhost:9998/tika'
        self.is_ready = False
        self.decimal_round = '{0:.10f}'

    @staticmethod
    def strip_accents(text):
        return ''.join(char for char in unicodedata.normalize('NFKD', text) if unicodedata.category(char) != 'Mn')

    def _cleanup(self):
        """
        Removes old dirs.
        """

        if os.path.exists(self.pdfs_processing_dir):
            rmtree(self.pdfs_processing_dir)

        if os.path.exists(self.json_path):
            rmtree(self.json_path)

        if os.path.exists(self.plots_path):
            rmtree(self.plots_path)

    def _prepare_pdfs(self):
        """
        General method to find recursively PDFs.
        """

        return sorted(
            list(
                set(
                    [os.path.join(r, f) for r, dirs, fs in os.walk(self.path) for f in fs if
                     f.endswith('.pdf') and os.path.getsize(os.path.join(r, f)) > 0]
                )
            ),
            key=os.path.getsize,
            reverse=True
        )

    def _create_dirs(self):
        """
        Creates output directories for processed data.
        """

        try:
            if not os.path.exists(self.pdfs_processing_dir):
                os.makedirs(self.pdfs_processing_dir)

            if not os.path.exists(self.json_path):
                os.makedirs(self.json_path)

            if not os.path.exists(self.plots_path):
                os.makedirs(self.plots_path)

        except OSError:
            raise ('Problem with creating new directories!')

    def _save_final_stats(self):
        """
        Returns finals stats for processed files.
        """

        self.is_ready = True

        save_path = '{processing_stats_dir}/final_stats.json'.format(
            processing_stats_dir=self.json_path
        )

        with open(save_path, 'w') as f:
            json.dump(
                self.final_stats_dict,
                f,
                sort_keys=True,
                indent=4,
                ensure_ascii=False
            )

    def _save_mining_time(self, item, test_type):
        """
        Stores in file time of processing pdf item.
        """

        self.mining_time_filename = '{test_type}.txt'.format(
            test_type=test_type
        )

        save_path = './{processing_dir}/{filename}'.format(
            processing_dir=self.pdfs_processing_dir,
            filename=self.mining_time_filename
        )

        with open(save_path, 'a') as f:
            f.write('{item1};{item2}\n'.format(
                item1=item[0],
                item2=item[1]
            ))

    def _test_regex(self):
        """
        Test 1 - Using regex.
        """

        _regex_pattern = re.compile(
            b"/Type\s*/Page([^s]|$)",
            re.MULTILINE | re.DOTALL
        )

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = LibrariesTesting.strip_accents(os.path.basename(pdf_file))

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    _pdf_data = f.read()

                    pages_count = len(_regex_pattern.findall(_pdf_data))

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='regex'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.OKBLUE + '[REGEX] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except (KeyError, AttributeError) as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='regex'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        regex_total_pages = sum(total_pages)

        print(
            Colors.OKBLUE + '[REGEX] Total pages count: {regex_total_pages}'.format(
                regex_total_pages=regex_total_pages
            ) + Colors.ENDC
        )

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        self.final_stats_dict.update(**{
            'regex_total_pages': regex_total_pages,
            'regex_total_parsing_time': total_parsing_time,
            'regex_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    def _test_pypdf2(self):
        """
        Test 2 - Using PyPDF2.
        Source: https://pythonhosted.org/PyPDF2/
        """

        print(Colors.UNDERLINE + '________________________________________________\n' + Colors.ENDC)

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = LibrariesTesting.strip_accents(os.path.basename(pdf_file))

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    reader = PdfFileReader(f)

                    pages_count = reader.getNumPages()

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='pypdf2'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.OKGREEN + '[PyPDF2] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except PdfReadError as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='pypdf2'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        pypdf2_total_pages = sum(total_pages)

        print(
            Colors.OKGREEN + '[PyPDF2] Total pages count: {pypdf2_total_pages}'.format(
                pypdf2_total_pages=pypdf2_total_pages
            ) + Colors.ENDC
        )

        self.final_stats_dict.update(**{
            'pypdf2_total_pages': pypdf2_total_pages,
            'pypdf2_total_parsing_time': total_parsing_time,
            'pypdf2_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    def _test_pdfrw(self):
        """
        Test 3 - Using pdfrw.
        Source: https://github.com/pmaupin/pdfrw
        """

        print(Colors.UNDERLINE + '________________________________________________\n' + Colors.ENDC)

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = LibrariesTesting.strip_accents(os.path.basename(pdf_file))

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    reader = PdfReader(f)

                    pages_count = reader.numPages

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='pdfrw'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.BOLD + '[PDFRW] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except (ValueError, PdfReadError) as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='pdfrw'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        pdfrw_total_pages = sum(total_pages)

        print(
            Colors.BOLD + '[PDFRW] Total pages count: {pdfrw_total_pages}'.format(
                pdfrw_total_pages=pdfrw_total_pages
            ) + Colors.ENDC
        )

        self.final_stats_dict.update(**{
            'pdfrw_total_pages': pdfrw_total_pages,
            'pdfrw_total_parsing_time': total_parsing_time,
            'pdfrw_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    def _test_pdfquery(self):
        """
        Test 4 - Using pdfquery.
        Source: https://github.com/jcushman/pdfquery
        """

        print(Colors.UNDERLINE + '________________________________________________\n' + Colors.ENDC)

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = LibrariesTesting.strip_accents(os.path.basename(pdf_file))

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    reader = PDFQuery(f)

                    pages_count = reader.doc.catalog['Pages'].resolve()['Count']

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='pdfquery'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.FAIL + '[PDFQUERY] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except (KeyError, AttributeError, TypeError, PDFSyntaxError, PDFEncryptionError) as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='pdfquery'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        pdfquery_total_pages = sum(total_pages)

        print(
            Colors.FAIL + '[PDFQUERY] Total pages count: {pdfquery_total_pages}'.format(
                pdfquery_total_pages=pdfquery_total_pages
            ) + Colors.ENDC
        )

        self.final_stats_dict.update(**{
            'pdfquery_total_pages': pdfquery_total_pages,
            'pdfquery_total_parsing_time': total_parsing_time,
            'pdfquery_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    def _test_tika(self):
        """
        Test 5 - Using tika.
        """

        print(Colors.UNDERLINE + '________________________________________________\n' + Colors.ENDC)

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = LibrariesTesting.strip_accents(os.path.basename(pdf_file))

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    reader = parser.from_buffer(
                        string=f.read(),
                        serverEndpoint=self.tika_url
                    )

                    pages_count = reader.get('metadata').get('xmpTPg:NPages', 0)

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='tika'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.HEADER + '[APACHE TIKA] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except (KeyError, AttributeError, TypeError, PDFSyntaxError, PDFEncryptionError) as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='tika'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        tika_total_pages = sum(total_pages)

        print(
            Colors.HEADER + '[APACHE TIKA] Total pages count: {tika_total_pages}'.format(
                tika_total_pages=tika_total_pages
            ) + Colors.ENDC
        )

        self.final_stats_dict.update(**{
            'tika_total_pages': tika_total_pages,
            'tika_total_parsing_time': total_parsing_time,
            'tika_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    def _test_pdfminer(self):
        """
        Test 6 - Using PDFMiner.
        """

        print(Colors.UNDERLINE + '________________________________________________\n' + Colors.ENDC)

        total_pages, errors, total_mining_time = [], [], []

        for index, pdf_file in enumerate(self.pdfs):
            index = index + 1

            filename = os.path.basename(pdf_file)

            file_size = self.convert_size(self.get_file_size(pdf_file))

            try:
                start_time = time.time()

                with open(pdf_file, 'rb') as f:
                    parser = PDFParser(f)

                    doc = PDFDocument(parser)
                    parser.set_document(doc)

                    pages = resolve1(doc.catalog['Pages'])
                    pages_count = pages.get('Count', 0)

                    end_time = time.time()

                    single_file_time = self.decimal_round.format(end_time - start_time)

                    total_mining_time.append(single_file_time)

                    mining_time = filename, single_file_time

                    self._save_mining_time(
                        item=mining_time,
                        test_type='pdfminer'
                    )

                    total_pages.append(pages_count)

                    print(
                        Colors.CYAN + '[PDFMINER] File {i}/{index}. Total pages: {pages_count} --> "{filename}" - {file_size}'.format(
                            i=index,
                            index=len(self.pdfs),
                            pages_count=pages_count,
                            filename=filename,
                            file_size=file_size
                        ) + Colors.ENDC
                    )
            except (KeyError, AttributeError, PDFSyntaxError, PDFEncryptionError)  as error:
                self._save_mining_time(
                    item=(filename, self.default_time),
                    test_type='pdfminer'
                )

                errors.append(error)
                pass

        total_pages, total_errors = list(map(int, total_pages)), len(errors)

        list_set_errors, total_parsing_time = list(set(errors)), sum(list(map(float, total_mining_time)))

        pdfminer_total_pages = sum(total_pages)

        print(
            Colors.CYAN + '[PDFMINER] Total pages count: {pdfminer_total_pages}'.format(
                pdfminer_total_pages=pdfminer_total_pages
            ) + Colors.ENDC
        )

        self.final_stats_dict.update(**{
            'pdfminer_total_pages': pdfminer_total_pages,
            'pdfminer_total_parsing_time': total_parsing_time,
            'pdfminer_errors': {
                'count': total_errors,
                'errors': list_set_errors
            },
        })

    @staticmethod
    def get_file_size(file_path):
        """
        Returns file size.
        """

        return os.stat(file_path).st_size

    @staticmethod
    def convert_size(size_bytes):
        """
        General method to convert bytes into human readable size.
        """

        if size_bytes is not None:
            if size_bytes == 0:
                return '0B'

            size_name = (
                'B',
                'KB',
                'MB',
                'GB',
                'TB'
            )

            i = int(math.floor(math.log(size_bytes, 1024)))

            p = math.pow(1024, i)

            s = round(size_bytes / p, 2)

            return '{filesize} {size_type}'.format(
                filesize=s,
                size_type=size_name[i]
            )

        return 0

    def launch(self):
        """
        Runs a pipeline.
        """

        self._cleanup()
        self._create_dirs()
        self._test_regex()
        self._test_pypdf2()
        self._test_pdfrw()
        self._test_pdfquery()
        self._test_tika()
        self._test_pdfminer()
        self._save_final_stats()
