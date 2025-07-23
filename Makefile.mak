CC=gcc
CFLAGS=-Wall -Wextra -std=c99
LDFLAGS=-lm

all: prime

prime: main.o prime.o function.o
	$(CC) $(CFLAGS) -o prime main.o prime.o function.o $(LDFLAGS)

main.o: main.c prime.h function.h

prime.o: prime.c prime.h

function.o: function.c function.h

clean:
	rm -f prime *.o
