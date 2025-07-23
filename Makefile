CC=gcc
CFLAGS=-Wall -Wextra -std=c99
LDFLAGS=-lm

all: prime

prime: prime.c
	$(CC) $(CFLAGS) -o prime prime.c $(LDFLAGS)

clean:
	rm -f prime
