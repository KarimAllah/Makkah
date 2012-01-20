
.globl _start

_start:
	mov r1, #1
	mov r2, #2
	cmp r2, r1
	bgt first_test
	cmp r1, r2
	blt second_test
	mov r5, #1
	mov r6, #2
	orr r7, r5, r6
	orr r6, r5, #2
	lsl r5, r5, #3
first_test:
	b	.
second_test:
	b	.
	lsr r5, r5, #3
	cmp r1, r6
	bl  myself
	beq myself
	mov r6, r5
	ldr r5, value_x
	bfc r5, #1, #3
	str r6, [r5, r0]
	ldr r5, value_y
	str r6, [r5]
	add r6, r6, #4
	sub r5, r5, r5
	add r5, r5, r5
myself:
	mov r6, #14
	ldr r5, myself

	ldr r0, =(_offset)
	ldr r1, =(0x40300000)
	add r0, r0, r1
	mcr p15, 0, r0, c12, c0, 0
	svc 0x1

	b	.

value_x:
	.long	(0xF)

value_y:
	.long	(0x40300000 + 0x54)

.align 5
_offset:
	b	.
	b	.
	b	.
	b	.
	b	.
	b	.
