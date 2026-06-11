import pyrtl

# ucsbcs154lab3
# All Rights Reserved
# Copyright (c) 2023 Regents of the University of California
# Distribution Prohibited


# Initialize your memblocks here:
i_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, max_read_ports=2, max_write_ports=1)
d_mem = pyrtl.MemBlock(bitwidth=32, addrwidth=32, max_read_ports=2, max_write_ports=1, asynchronous=True)
rf = pyrtl.MemBlock(bitwidth=32, addrwidth=5, max_read_ports=2, max_write_ports=1, asynchronous=True)

pc = pyrtl.Register(bitwidth = 32, name = 'pc') # zero by default




instr = pyrtl.WireVector(bitwidth=32, name='instr')
op = pyrtl.WireVector(bitwidth=6, name='op')
rs = pyrtl.WireVector(bitwidth=5, name='rs')
rt = pyrtl.WireVector(bitwidth=5, name='rt')
rd = pyrtl.WireVector(bitwidth=5, name='rd')
sh = pyrtl.WireVector(bitwidth=5, name='sh')
func = pyrtl.WireVector(bitwidth=6, name='func')
imm = pyrtl.WireVector(bitwidth=16, name='imm')
alu_out = pyrtl.WireVector(bitwidth=32, name='alu_out')


regDst = pyrtl.WireVector(bitwidth=1, name='regDst')
branch = pyrtl.WireVector(bitwidth=1, name='branch')
memToReg = pyrtl.WireVector(bitwidth=1, name='memToReg')
aLUOp = pyrtl.WireVector(bitwidth=3, name='aLUOP')
memWrite = pyrtl.WireVector(bitwidth=1, name='memWrite')
aLUSrc = pyrtl.WireVector(bitwidth=2, name='aLUSrc')
regWrite = pyrtl.WireVector(bitwidth=1, name='regWrite')


instr <<= i_mem[pc]



# When working on large designs, such as this CPU implementation, it is
# useful to partition your design into smaller, reusable, hardware
# blocks. We have indicated where you should put different hardware blocks
# to help you get write your CPU design. You have already worked on some
# parts of this logic in prior labs, like the decoder and alu.


## DECODER
# decode the instruction
op <<= instr[26:32]
imm  <<= instr[0:16]
rs <<= instr[21:26]
rt <<= instr[16:21]
rd <<= instr[11:16]
sh <<= instr[6:11]
func <<= instr[0:6]



## CONTROLLER
# define control signals for the following instructions
# add, and, addi, lui, ori, slt, lw, sw, beq
#            REG_DST, BRANCH, REGWRITE, ALU_SRC (2-bits), MEM_WRITE, MEM_TO_REG, ALU_OP (3-bits)
# Add 000    1010000000
# Addi 000   0010100000
# AND 001    1010000001
# LUI 010    001xx00010
# OR 011     1010000011
# ORi 011    0011000011
# SLT 100    1010000100
# SUB 101    1010000101
# BEQ 101    X10000X101
# LW         0010101000
# SW         0000110000
# Register Operand 00
# Sign Extension 01
# Zero extension 10
#
with pyrtl.conditional_assignment:
    with op == 0: # Rtype, add, and, or, slt, sub,
        regDst |= 1
        branch |= 0
        regWrite |= 1
        aLUSrc |= 0
        memWrite |= 0
        memToReg |= 0
        with func == 32: #add
            aLUOp |= 0
        with func == 34: #sub
            aLUOp |= 5
        with func == 36: #and
            aLUOp |= 1
        with func == 37: #or
            aLUOp |= 3
        with func == 42: #slt
            aLUOp |= 4
    with op == 4: # beq
        regDst |= 0
        branch |= 1
        regWrite |= 0
        aLUSrc |= 0
        memWrite |= 0
        memToReg |= 0
        aLUOp |= 5
    with op == 8: #addi
        regDst |= 0
        branch |= 0
        regWrite |= 1
        aLUSrc |= 1
        memWrite |= 0
        memToReg |= 0
        aLUOp |= 0
    with op == 13: # ori
        regDst |= 0
        branch |= 0
        regWrite |= 1
        aLUSrc |= 2
        memWrite |= 0
        memToReg |= 0
        aLUOp |= 3
    with op == 15: # lui
        regDst |= 0
        branch |= 0
        regWrite |= 1
        aLUSrc |= 2  # doesn't matter
        memWrite |= 0
        memToReg |= 0
        aLUOp |= 2
    with op == 35: # lw
        regDst |= 0
        branch |= 0
        regWrite |= 1
        aLUSrc |= 1
        memWrite |= 0
        memToReg |= 1
        aLUOp |= 0
    with op == 43: # sw
        regDst |= 0
        branch |= 0
        regWrite |= 0
        aLUSrc |= 1
        memWrite |= 1
        memToReg |= 0
        aLUOp |= 0

## WRITE REGISTER mux
# create the mux to choose among rd and rt for the write register

writeReg = pyrtl.WireVector(bitwidth=5, name='writeReg')

with pyrtl.conditional_assignment:
    with regDst == 0:
        writeReg |= rt
    with regDst == 1:
        writeReg |= rd


## READ REGISTER VALUES from the register file
# read the values of rs and rt registers from the register file
readData1 = pyrtl.WireVector(bitwidth=32, name='readData1')
readData2 = pyrtl.WireVector(bitwidth=32, name='readData2')

readData1 <<= rf[rs]
readData2 <<= rf[rt]


## ALU INPUTS
# define the ALU inputs after reading values of rs and rt registers from
# the register file
# Hint: Think about ALU inputs for instructions that use immediate values

alu_in1 = pyrtl.WireVector(bitwidth=32, name='alu_in1')
alu_in2 = pyrtl.WireVector(bitwidth=32, name='alu_in2')

alu_in1 <<= readData1
with pyrtl.conditional_assignment:
    with aLUSrc == 0:
        alu_in2 |= readData2
    with aLUSrc == 1:
        alu_in2 |= imm.sign_extended(32)
    with aLUSrc == 2:
        alu_in2 |= imm.zero_extended(32)

## FIND ALU OUTPUT
# find what the ALU outputs are for the following instructions:
# add, and, addi, lui, ori, slt, lw, sw, beq
# Hint: you want to find both ALU result and zero. Refer the figure in the
# lab document

#ALU
with pyrtl.conditional_assignment:
    with aLUOp == 0: # add
        alu_out |= pyrtl.corecircuits.signed_add(alu_in1,alu_in2)
    with aLUOp == 1: #and
        alu_out |= alu_in1 & alu_in2
    with aLUOp == 2: #lui
        alu_out |= pyrtl.corecircuits.concat(alu_in2[0:16], alu_in1[0:16])
    with aLUOp == 3: #or
        alu_out |= alu_in1 | alu_in2
    with aLUOp == 4: #slt
        alu_out |= pyrtl.corecircuits.signed_lt(alu_in1, alu_in2)
    with aLUOp == 5: #sub
        alu_out |= pyrtl.corecircuits.signed_sub(alu_in1,alu_in2)

#ALU Zero line w/ logic
zero = pyrtl.WireVector(bitwidth=32, name='zero')
with pyrtl.conditional_assignment:
    with alu_out == 0:
        zero |= 1
    with pyrtl.otherwise:
        zero |= 0


## DATA MEMORY WRITE
# perform the write operation in the data memory. Think about which
# instructions will need to write to the data memory
d_mem[alu_out] <<= pyrtl.memory.MemBlock.EnabledWrite(readData2, enable=memWrite)


## REGISTER WRITEBACK
# Create the mux to select between ALU result and data memory read.
# Writeback the selected value to the register file in the
# appropriate write register


writeDataReg = pyrtl.WireVector(bitwidth=32, name='writeDataReg')
with pyrtl.conditional_assignment:
    with writeReg == 0: # makes sure $zero is never not 0
        writeDataReg |= 0
    with memToReg == 0:
        writeDataReg |= alu_out
    with memToReg == 1:
        writeDataReg |= d_mem[alu_out]

rf[writeReg] <<= pyrtl.memory.MemBlock.EnabledWrite(writeDataReg, enable=regWrite)


## PC UPDATE
# finally update the program counter. Pay special attention when updating
# the PC in the case of a branch instruction.




with pyrtl.conditional_assignment:
    with branch == 1:
        with zero == 1:
            pc.next |= pc + imm.sign_extended(32) + 1
        with pyrtl.otherwise:
            pc.next |= pc + 1
    with pyrtl.otherwise:
        pc.next |= pc + 1


if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file. You can use the
       "mips_to_hex.sh" file provided to assemble your MIPS program to
       corresponding hexadecimal instructions.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. Another assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that all instructions of the program are executed.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(100):
        sim.step({})

    # Use render_trace() to debug if your code doesn't work.
    sim_trace.render_trace(symbol_len=2, repr_func=str)

    # You can also print out the register file or memory like so if you want to debug:
    #print(sim.inspect_mem(d_mem))
    #print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    assert(sim.inspect_mem(d_mem)[0] == 10)
    assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    print('Passed!')
