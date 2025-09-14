import re
from PIL import Image
import numpy as np
import argparse
import sys
from pathlib import Path


parser = argparse.ArgumentParser(description="Process a text file and optionally an image file.")
parser.usage = "sample instruction: python compiler.py snake.txt snake.png"

parser.add_argument("programFile", type=Path, help="Path to the text file")
parser.add_argument("-i", type=Path, nargs="?", default=None, help="Optional path to an image file")
parser.add_argument("-o", type=Path, nargs="?", default="a.txt", help="Optional path to an output adress")

args = parser.parse_args()

if not args.programFile.exists():
    print(f"Error: program file '{args.text_file}' not found.")
    sys.exit()


lines = []
hm = {}


with open(args.programFile, 'r') as file: # reads in file defines labels and consts

    for line in file:
        line = line.strip().lower()
        line = re.sub(",","",line)
        words = line.split()
        if len(words)==0: continue
        if line[0]=="\\":
            continue
        if words[0]=="const":
            hm[words[1]] = int(words[3])
            continue
        if line[-1] == ':':
            hm[line[:-1]] = len(lines)
            lines.append(line)
            continue

        lines.append(words)


if args.i:
    if not args.i.exists():
        print(f"Error: Image file '{args.image_file}' not found.")
        sys.exit()
    img = Image.open(args.i)
    img = img.resize((4, 4), resample=0)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    arr = np.asarray(img)
    arr2 =[]
    for row in arr:
        for pix in row:
            arr2.append(pix[0] // 85 + ((pix[1]//85)<<2)+((pix[2]//85)<<4))
else: 
    arr2 = [63 for _ in range(16)]

arr3=[0]
for i, v in enumerate(arr2):
    b = (i+3)%5
    if b==0: arr3.append(0)
    arr3[-1]+=(np.int64(v))<<(10*b)




def placeVal(val, postion):
    if(isinstance(val, str) and val[0]=="r" and len(val) == 2): val = int(val[1])
    elif(isinstance(val, str) and val[0]=="#"): val = int(val[1:])
    elif(isinstance(val, str)): 
        try: val = hm[val]
        except: pass

    return int(val)*pow(2,postion)

def mov(line):
    if(line[1][0]=="r" and line[2][0]=="r"):
        return 3+placeVal(line[1],7)+placeVal(line[1],10)
    
def memToVal(inp):
    inp = inp[1:-1]
    vals = inp.split("+")
    reg =0
    imm =0
    for val in vals:
        if val[0]=="r": reg = int(val[1])
        elif val[0]=="#": imm = int(val[1:])
    return reg, imm



    
### inputs to machine code ###
def regop(op, line):
    return regIns(op, line[1], line[2], line[3], 0)
def regIns(op, dest, rA, rB, check):
    return([op+placeVal(dest,7)+placeVal(rB,3)+placeVal(rA,10)+placeVal(check,6)])


def immop3(op, line): #immediate value is third arg
    return immIns(op, line[1], line[2], line[3])
def immop2(op, line): #immediate value is second arg
    return immIns(op, line[1], line[3], line[2])
def immIns(op, dest, rA, imm):
    return [(op+ placeVal(dest,7)+placeVal(rA,10)+placeVal(1,6)), placeVal(imm,0)]

def branchop(op,line):
    return branchIns(op, line[1], line[2], line[3], len(line[0])==4)
def branchIns(op, rA, rB, addr, link):
    return [(op+ placeVal(rB,7)+placeVal(rA,10)+placeVal(1,6)), placeVal(link,12)+placeVal(addr,0)]


def strop(op, line):
    rC, offset = memToVal(line[1])
    return strIns(op, line[2],line[3],rC, offset)
def strIns(op, rA, rB, rC, offset):
    return [op+ placeVal(rB,7)+placeVal(rA,10)+placeVal(1,6), placeVal(offset, 0)+placeVal(rC,10)]

def lodop2(op,line): # mem is arg 2
    rC, offset = memToVal(line[2])
    return lodIns(op, line[1], line[3],rC, offset)
def lodop3(op,line): # mem is arg 3
    rC, offset = memToVal(line[3])
    return lodIns(op, line[1], line[2],rC, offset)
    
def lodIns(op, dest, rA, rC, offset):
    return [op+ placeVal(dest,7)+placeVal(rA,10)+placeVal(1,6), placeVal(offset, 0)+placeVal(rC,10)]

##

def inIns(line):
    dest = line[1]
    port = line[2]
    return [43+ placeVal(dest,7)+placeVal(port,10)+placeVal(1,6)]

def stackIns(line):
    if(line[0]=="pop"):
        op = 3
    else: op = 2
    return[op+placeVal(1,6)+placeVal(line[1],10)]

def impliedIns(line):
    options = ["halt", "nop", "fcb", "ssf", "usf", "ret"]
    for i,v in enumerate(options):
        if v==line[0]:
            op = i
    return[45+placeVal(1,6)+placeVal(op,10)]

def cbfIns(line):
    if(len(line)==6):
        rA = line[1]
        rB = line[2]
        rC = line[3]
        X = line[4][1:]
        Y = line[5][1:]
    elif(line[2][0]=="r"):
        rA = 0
        rB = 0
        rC = line[1]
        X = line[2]
        Y = line[3]
    else:
        rA = line[1]
        rB = line[2]
        rC = line[3]
    
    return [49+ placeVal(rB,7)+placeVal(rA,10)+placeVal(1,6), placeVal(Y, 0)+placeVal(rC,10)+ placeVal(X, 5)]

def outIns(line):
    io = line[1]
    rA =  line[2]
    return [52+ placeVal(io,7)+placeVal(rA,10)+placeVal(1,6)]

def progIns(line):
    if line[0] == "proghead": op = 51
    if line[0] == "progload": op = 50
    prog = line[1]
    return [op+placeVal(prog,10)+placeVal(1,6)]
##################


def REG(line):
    match line[0]:
        case "sub": return regop(0, line)
        case "div": return regop(1, line)
        case "rem": return regop(2, line)
        case "add": return regop(3, line)
        case "mul": return regop(4, line)
        case "and": return regop(5, line)
        case "or": return regop(6, line)
        case "xor": return regop(7, line)

        case "not": return regIns(0, line[1], line[2], 0, 1)
        case "lsr": return regIns(1, line[1], line[2], 0, 1)
        case "mov": return regIns(3, line[1], line[2], 0, 0)

def STR(line):
    rC, offset = memToVal(line[1])
    match line[0]:
        case "sub": return strop(10, line)
        case "div": return strop(11, line)
        case "rem": return strop(12, line)
        case "add": return strop(13, line)
        case "mul": return strop(14, line)
        case "and": return strop(15, line)
        case "or": return strop(16, line)
        case "xor": return strop(17, line)

        case "not": return strIns(18, line[2], 0, rC, offset)
        case "lsr": return strop(19, line)
        case "lsr": return strop(20, line)
        case "mov": return strIns(13, line[2], 0, rC, offset)

def LOD(line):
    
    if len(line)==4 and (line[3][0]=="["):
        match line[0]:
            case "sub": return lodop3(21, line)
            case "div": return lodop3(22, line)
            case "rem": return lodop3(23, line)
            case "add": return lodop3(24, line)
            case "mul": return lodop3(25, line)
            case "and": return lodop3(26, line)
            case "or": return lodop3(27, line)
            case "xor": return lodop3(28, line)
    else:
        match line[0]:
            case "sub": return lodop2(21, line)
            case "div": return lodop2(22, line)
            case "rem": return lodop2(23, line)
            case "add": return lodop2(24, line)
            case "mul": return lodop2(25, line)
            case "and": return lodop2(26, line)
            case "or": return lodop2(27, line)
            case "xor": return lodop2(28, line)

            case "lsr": return lodop2(30, line)
            case "lsl": return lodop2(31, line)
            case "sub": return lodop2(32, line)
            case "div": return lodop2(33, line)
            case "rem": return lodop2(34, line)
            case "not": return lodIns(29, line[1], 0, memToVal(line[2])[0], memToVal(line[2])[1])
            case "mov": return lodIns(24, line[1], 0, memToVal(line[2])[0], memToVal(line[2])[1])  

def IMM(line):
    if(line[2][0]=="#"):
        imm = int(line[2][1:])
        
        match line[0]:
            case "sub": return immop2(46, line)
            case "div": return immop2(47, line)
            case "rem": return immop2(48, line)
            case "add": return immop2(38, line)
            case "mul": return immop2(39, line)
            case "and": return immop2(40, line)
            case "or": return immop2(41, line)
            case "xor": return immop2(42, line)

            case "lsr": return immop2(44, line)
            case "lsl": return immIns(39, line[1], line[2], pow(2,imm))
            case "mov": return immIns(38, line[1], 0, imm)
        
    elif(line[3][0]=="#"):
        imm = int(line[3][1:])
        match line[0]:
            case "sub": return immop3(35, line)
            case "div": return immop3(36, line)
            case "rem": return immop3(37, line)
            case "add": return immop3(38, line)
            case "mul": return immop3(39, line)
            case "and": return immop3(40, line)
            case "or": return immop3(41, line)
            case "xor": return immop3(42, line)

            case "lsr": return immop3(44, line)
            case "lsl": return immIns(39, line[1], line[2], pow(2,imm))
            case "mov": return immIns(38, line[1], 0, imm)

def branch(line):
    match line[0][:3]:
        case "bgt": return branchop(5, line)
        case "bge": return branchop(6, line)
        case "beq": return branchop(7, line)
        case "bne": return branchop(8, line)
        case "bal": return branchIns(7, 0, 0, line[1], len(line[0])==4)
        case "ble": return branchIns(6, line[2],line[1],line[3],len(line[0])==4)
        case "blt": return branchIns(5, line[2],line[1],line[3],len(line[0])==4)
   

        
    



for i in range(0,2):
    instructions = []
    for index, line in enumerate(lines):
        if line[-1] == ":": 
            length = 0
            for ins in instructions: length+=len(ins)
            hm[line[:-1]] = length+16
            continue
        try:
            if instructions[-1] == None: print("theres something wrong with: "+lines[index-1])
        except: pass
        if line[0][0]=="b":
                instructions.append(branch(line))
        elif line[0]=="in": instructions.append(inIns(line))
        elif line[0]=="push" or line[0]=="pop": instructions.append(stackIns(line))
        elif line[0] in ["halt", "nop", "fcb", "ssf", "usf", "ret"]: instructions.append(impliedIns(line))
        elif line[0] == "cbf":  instructions.append(cbfIns(line))
        elif line[0] == "out": instructions.append(outIns(line))
        elif line[0] == "proghead" or line[0] == "progload": instructions.append(progIns(line))




        elif( len(line)==4):
            if (line[1][0]=="r" and line[2][0]=="r" and line[3][0]=="r"):
                instructions.append(REG(line))
            
            elif (line[1][0]=="[" and line[2][0]=="r" and line[3][0]=="r"):
                instructions.append(STR(line))
            
            elif (line[1][0]=="r" and (line[2][0]=="[" or line[3][0]=="[")):
                instructions.append(LOD(line))
            
            elif (line[1][0]=="r" and (line[3][0]=="#" or line[2][0]=="#")):
                instructions.append(IMM(line))
        
        elif(len(line) ==3):
            if (line[1][0]=="r" and line[2][0]=="r"):
                instructions.append(REG(line))
            elif (line[1][0]=="r" and line[2][0]=="#"):
                instructions.append(IMM(line))
            elif (line[1][0]=="r" and line[2][0]=="["):
                instructions.append(LOD(line))
            elif (line[1][0]=="[" and line[2][0]=="r"):
                instructions.append(STR(line))

i=3
machineCode=arr3
machineCode[0]+= (branch(["bal", "start"])[0])+(branch(["bal", "start"])[1]<<13)


for instruction in instructions:
    
    for word in instruction:
        if i == 4:
            machineCode.append(0)
            i=0
        machineCode[-1]+=word<< (13*i)
        i+=1


with open(args.o, "w", encoding="utf-8") as f:
    for instruction in machineCode:
        f.write(f"{instruction}\n")
