import re
import os
import itertools
import numpy as np
import pandas as pd
import pickle as pkl
import os.path as op
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import Counter, OrderedDict


class RGramMaker():
    
    def __init__(self, alphabet, min_num=None, max_alph_length=None, separator=","):
        assert min_num or max_alph_length
        self.A = [a for a in alphabet]
        self.starting_alphabet = [a for a in alphabet]
        self.in_l = len(self.A)
        self.MN = min_num
        self.MAL = max_alph_length
        self.separator = separator
        self.B = OrderedDict()
        self.i_num = 0
        
    def __add__(self, other):
        assert self.MN == other.MN
        assert self.MAL == other.MAL
        assert self.separator == other.separator
        joined_alphabet = "".join(list(np.union1d(self.starting_alphabet, other.starting_alphabet)))
        the_sum = RGramMaker(joined_alphabet, min_num=self.MN, max_alph_length=self.MAL, separator=self.separator)
        decompressed1 = [self.separate(a[1]) for a in self.decompressed()]
        decompressed2 = [self.separate(a[1]) for a in other.decompressed()]
        d_union = sorted(np.union1d(decompressed1, decompressed2), key=len)
        for i,a in enumerate(d_union):
            the_sum.B[str(i)] = a
        the_sum.A.extend(list(the_sum.B.keys()))
        return(the_sum)
    
    def __radd__(self, other):
        return(self)
    
    @staticmethod
    def most_common_pair(sequence):
        counter = {}
        MCP = None
        MCP_c = 0
        l = len(sequence)
        if l > 1000000:
            print("Verbose mode for sequence of length "+str(l))
        for a in range(l-1):
            current = "".join(sequence[a:a+2])
            if current not in counter:
                counter[current] = 1
            else:
                counter[current] += 1
            if counter[current] > MCP_c:
                MCP = current
                MCP_c = counter[current]
            if a % 10000000 == 0:
                print("Pair #"+str(a))
        return([a for a in MCP], MCP_c)
        
    def separate(self, string_l, flank=True):
        s = self.separator.join(string_l)
        if flank:
            s = self.separator+s+self.separator
        return(s)
        
    def compress_iter(self, string):
        i = 0
        sep_str = list(filter(lambda x: x != "", string.split(self.separator)))
        if len(sep_str) == 1:
            return(string)
        else:
            #pairs = []
            #while i != len(sep_str)-1:
            #    new_pair = self.separate([sep_str[i], sep_str[i+1]], False)
            #    pairs.append(new_pair)
            #    i += 1
            most_common_pair, mcp_n = RGramMaker.most_common_pair(sep_str)#Counter(pairs).most_common(1)[0]
            if most_common_pair not in self.B.values():
                if mcp_n >= self.MN:
                    new_letter = str(self.i_num)
                    self.i_num += 1
                    result_string = string.replace(","+most_common_pair+",", ","+new_letter+",")
                    self.A.append(new_letter)
                    self.B[new_letter] = most_common_pair
                    return(result_string)
                else:
                    return(string)
            else:
                new_letter = {self.B[a]:a for a in self.B}[most_common_pair]
                result_string = string.replace(","+most_common_pair+",", ","+new_letter+",")
                return(result_string)
    
    def compress(self, string):
        i = 0
        criterium = True
        result_string = self.separate([a for a in string])
        prev_len = len(result_string)
        while True:
            result_string = self.compress_iter(result_string)
            i += 1
            if self.MAL:
                if len(self.A)-self.in_l >= self.MAL:
                    break
            else:
                if len(result_string) == prev_len:
                    break
                else:
                    prev_len = len(result_string)
        return(result_string)
    
    def decompress_iter(self, sep_str):
        new_str = []
        for a in sep_str:
            if a in self.B:
                new_str.append(self.B[a])
            else:
                new_str.append(a)
        return(self.separate(new_str))
    
    def decompress(self, string):
        new_string = string
        while True:
            sep_str = list(filter(lambda x: x != "", new_string.split(self.separator)))
            d = len(set(sep_str).difference(set(self.A[0:self.in_l])))
            #print(d)
            if d == 0:
                break
            else:
                new_string = self.decompress_iter(sep_str)
        return(new_string.replace(self.separator, ""))
    
    def decompressed(self):
        dk = list(reversed(sorted(self.B.items(), key=lambda x: len(self.decompress(x[0])))))
        dk = [(a[0],self.decompress(a[0])) for a in dk]
        return(dk)
    
    def segment(self, string, max_len=100):
        ts = string[:]
        for num,rg in self.decompressed():
            ts = ts.replace(rg, ","+num+"|rgram,")
        tl = list(filter(lambda x: len(x)>0 and len(x)<max_len, ts.split(",")))
        result = []
        for seg in tl:
            if "rgram" in seg:
                result.append(
                    self.decompress(seg.split("|")[0])
                )
            else:
                result.extend([letter for letter in seg])
        return(" ".join(result))