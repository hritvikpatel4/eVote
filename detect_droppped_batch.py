import sys

votes = set()

total_votes = int(sys.argv[1])
files = sys.argv[2:]

for i in range(1, total_votes+1):
    votes.add(i)

for i in range(len(files)):
    with open(files[i], "r") as fileptr:
        data = fileptr.readlines()[2:]

        for j in range(len(data)):
            if int(data[j].split(",")[2]) in votes:
                votes.remove(int(data[j].split(",")[2]))

print(votes)
