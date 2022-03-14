import sys
import random
import heapq
import numpy as np

class Piece:

    enemyTypes = ["King", "Queen", "Bishop", "Rook", "Knight"]

    movement = {"King": [(1, 1, 1), (1, 0, 1), (1, -1, 1), (0, -1, 1), (-1, -1, 1), (-1, 0, 1), (-1, 1, 1), (0, 1, 1)],
                "Rook": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0)],
                "Bishop": [(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Queen": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0), (1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Knight": [],
                "Obstacle": [],
                "Empty": [],
                }

    def __init__(self, pieceType: str) -> None:
        self.type = pieceType

    def isEmpty(self) -> bool:
        return self.type == "Empty"

    def possibleMovement(self):
        return self.movement[self.type]


class Board:


    def __init__(self, cols: int, rows: int, listOfObstacles, maxNumOfEachEnemy) -> None:
        self.enemyPos = {}  # (x, y) -> Enemy type
        self.obstaclePos = []
        self.board_size_x = cols
        self.board_size_y = rows
        self.maxNumOfEachEnemy = maxNumOfEachEnemy
        self.currentNumOfEachEnemy = [0, ] * len(maxNumOfEachEnemy)
        self.existsPositionWithNoLegalValues = False

        self.blocked = []
        for i in range(cols):
            self.blocked.append([False, ] * rows)
        
        self.possibleEnemyTypes = []
        sample = list(range(len(Piece.enemyTypes)))
        for i in range(cols):
            self.possibleEnemyTypes.append([])
            for j in range(rows):
                self.possibleEnemyTypes[i].append(sample.copy())
        
        # add the obstacles
        for x, y in listOfObstacles:
            self.addObstaclePiece(x, y)


    def addEnemyPiece(self, pieceType: str, x: int, y: int) -> None:
        self.enemyPos[(x, y)] = Piece(pieceType)
        self.blocked[x][y] = True
        self.possibleEnemyTypes[x][y] = [Piece.enemyTypes.index(pieceType)]
        self.currentNumOfEachEnemy[Piece.enemyTypes.index(pieceType)] += 1
        
    def addObstaclePiece(self, x: int, y: int) -> None:
        self.obstaclePos.append((x, y))
        self.blocked[x][y] = True
        self.possibleEnemyTypes[x][y] = []

    def isWithinBoard(self, x, y) -> bool:
        if (0 > x or x >= self.board_size_x) or (0 > y or y >= self.board_size_y):
            return False
        return True

    def isThreatened(self, x, y) -> bool:
        # Must update threatened first!!!
        return self.numOfEnemiesThreatening[x][y] > 0

    def isBlocked(self, x, y) -> bool:
        return (x, y) in self.obstaclePos or (x, y) in self.enemyPos.keys()

    def setThreatened(self, x, y) -> None:
        if (x, y) in self.enemyPos:
            self.numOfEnemiesThreatening[x][y] += 1

    def ac3(self, startingPosition = None):
        '''Starting position is in the format of (x, y)'''

        if startingPosition == None:
            frontier = set(self.enemyPos.keys())
            self.existsPositionWithNoLegalValues = False
        else:
            frontier = [startingPosition]
        
        while (len(frontier) != 0):
            x, y = frontier.pop()
            for possibleType in self.possibleEnemyTypes[x][y]:
                if self.maxNumOfEachEnemy[possibleType] == 0:
                    continue
                if Piece.enemyTypes[possibleType] == "Knight":
                    for twoSteps in [-2, 2]:
                        for oneStep in [-1, 1]:
                            if self.isWithinBoard(x + twoSteps, y+oneStep):
                                if (not possibleType in self.possibleEnemyTypes[x + twoSteps][y+oneStep]):
                                    continue

                                self.possibleEnemyTypes[x + twoSteps][y+oneStep].remove(possibleType)
                                frontier.add((x + twoSteps, y+oneStep))

                            if self.isWithinBoard(x + oneStep, y+twoSteps):
                                if (not possibleType in self.possibleEnemyTypes[x + oneStep][y + twoSteps]):
                                    continue

                                self.possibleEnemyTypes[x + oneStep][y + twoSteps].remove(possibleType)
                                frontier.add((x + oneStep, y+twoSteps))
                else:
                    transModel = pieceMovementModel(
                        self, x, y, Piece.movement[Piece.enemyTypes[possibleType]])
                    for possibleX, possibleY in transModel.getAllPossibleNewPos():
                        if (not possibleType in self.possibleEnemyTypes[possibleX][possibleY]):
                            continue
                        
                        self.possibleEnemyTypes[possibleX][possibleY].remove(possibleType)
                        frontier.add((possibleX, possibleY))
        
    def updateThreatened(self):

        # Reset number of pieces threatening a piece
        self.numOfEnemiesThreatening = []

        for i in range(self.board_size_x):
            self.numOfEnemiesThreatening.append([0, ] * self.board_size_y)

        for x, y in self.enemyPos:
            piece: Piece = self.enemyPos[(x, y)]
            if piece.type == "Knight":
                for twoSteps in [-2, 2]:
                    for oneStep in [-1, 1]:
                        if self.isWithinBoard(x + twoSteps, y+oneStep):
                            self.setThreatened(x+twoSteps, y+oneStep)
                        if self.isWithinBoard(x + oneStep, y+twoSteps):
                            self.setThreatened(x+oneStep, y+twoSteps)
            else:
                transModel = pieceMovementModel(
                    self, x, y, piece.possibleMovement())
                for possibleX, possibleY in transModel.getAllPossibleNewPos():
                    self.setThreatened(possibleX, possibleY)
        
        # calculate to find out the ranking of threatened
        self.numOfEnemiesThreatening_ranked = []
        for x, y in self.enemyPos:
            if self.numOfEnemiesThreatening[x][y] == 0:
                continue
            heapq.heappush(self.numOfEnemiesThreatening_ranked, (x, y))

        # apply AC-3 algorithm to all arcs
        self.ac3()
    
    def getTopThreatened(self, n: int):
        return heapq.nlargest(n, self.numOfEnemiesThreatening_ranked)

    def getMostThreatenedPos(self):
        highestThreatened = 0
        resultX, resultY = list(self.enemyPos.keys())[0]

        for x, y in self.enemyPos:
            # print(x, y, self.numOfEnemiesThreatening[x][y])
            if self.numOfEnemiesThreatening[x][y] > highestThreatened:
                highestThreatened = self.numOfEnemiesThreatening[x][y]
                resultX, resultY = x, y

        return (resultX, resultY, highestThreatened)

    def setGoal(self, K: int) -> None:
        self.K = K

    def goalCheck(self) -> bool:
        return len(self.enemyPos) >= self.K and self.sumOfThreatened() == 0
    
    def sumOfThreatened(self):
        sum = 0
        for x, y in self.enemyPos:
            sum += self.numOfEnemiesThreatening[x][y]
        return sum


class pieceMovementModel():

    def __init__(self, board: Board, x: int, y: int, piece_movements):
        self.x = x
        self.y = y
        self.board = board
        self.movements = piece_movements

    def moveToDirection(self, x_change: int, y_change: int):
        new_x = self.x + x_change
        new_y = self.y + y_change
        return (new_x, new_y)

    def getAllPossibleMovementToDirection(self, x_change: int, y_change: int, max_steps=0):
        '''Get all the positions that the piece can move to, including position that are being threatened by other pieces'''
        if max_steps == 0:
            max_steps = max(self.board.board_size_x, self.board.board_size_y)
        steps = []
        for i in range(max_steps):
            new_pos = self.moveToDirection((i+1) * x_change, (i+1) * y_change)
            if not self.board.isWithinBoard(new_pos[0], new_pos[1]):
                break
            if self.board.isBlocked(new_pos[0], new_pos[1]):
                steps.append(new_pos)
                break
            steps.append(new_pos)
        return steps

    def getAllPossibleNewPos(self):
        steps = []
        for movement in self.movements:
            xChange, yChange, maxSteps = movement
            steps.extend(self.getAllPossibleMovementToDirection(
                xChange, yChange, maxSteps))
        return steps

    def getAllAllowedMovementToDirection(self, x_change: int, y_change: int, max_steps=0):
        '''Get all the positions that the piece can move to without being threatened'''
        if max_steps == 0:
            max_steps = max(self.board.board_size_x, self.board.board_size_y)
        steps = []
        for i in range(max_steps):
            new_pos = self.moveToDirection((i+1) * x_change, (i+1) * y_change)
            if not self.board.isWithinBoard(new_pos[0], new_pos[1]) or self.board.isBlocked(new_pos[0], new_pos[1]):
                break
            if self.board.isThreatened(new_pos[0], new_pos[1]):
                continue
            steps.append(new_pos)
        return steps

    def getAllAllowedNewPos(self):
        steps = []
        for movement in self.movements:
            xChange, yChange, maxSteps = movement
            steps.extend(self.getAllAllowedMovementToDirection(
                xChange, yChange, maxSteps))
        return steps

class State:

    def __init__(self, rows, cols, listOfObstacles, numOfEachEnemies) -> None:
        self.board = Board(cols, rows, listOfObstacles, numOfEachEnemies)
        self.rows = rows
        self.cols = cols
        self.listOfObstacles = listOfObstacles
        self.numOfEachEnemies = numOfEachEnemies
        # self.currentAssignment = Assignment(numOfEachEnemies)
        
    def setAssignment(self, assignment: dict):
        self.board = Board(self.cols, self.rows, self.listOfObstacles, self.numOfEachEnemies)
        for pos in assignment:
            self.board.addEnemyPiece(assignment[pos], pos[0], pos[1])

    def inference(self, enemyType: str, position: tuple) -> bool:
        self.board.addEnemyPiece(enemyType, position[0], position[1])
        self.board.updateThreatened()
        print("Before inference, remaining possible number of pieces:")
        print(np.array([[len(x) for x in row] for row in self.board.possibleEnemyTypes]))
        for x in range(self.cols):
            for y in range(self.rows):
                print("Checking at", x, y, "which has", self.board.possibleEnemyTypes[x][y], self.board.isBlocked(x, y))
                if len(self.board.possibleEnemyTypes[x][y]) == 0 and (
                    not self.board.isBlocked(x, y)):
                    return False
        return True

    def setBoard(self, board: Board) -> None:
        self.board = board

def letterToX(character) -> int:
    return ord(character) - ord('a')

def PosToXY(pos) -> tuple:
    return (letterToX(pos[0]), int(pos[1:]))

def XYtoPos(xy: tuple) -> tuple:
    xCharVal: int = xy[0]+ord('a')
    return (chr(xCharVal), xy[1])

def parser(testfile):
    f = open(testfile, "r")

    def input():
        line = f.readline().strip("\n")
        return line

    rows = int(input().split(":")[1])
    cols = int(input().split(":")[1])
    # game = State()
    # game.initBoard(cols, rows)
    numOfObstacles = int(input().split(":")[1])
    listOfObstacles = []
    if numOfObstacles != 0:
        posOfObstacles = input().split(":")[1].split(" ")
        for obstacle in posOfObstacles:
            x, y = PosToXY(obstacle)
            listOfObstacles.append((x, y))
    else:
        input()

    # enemies
    numOfEachEnemies = input().split(":")[1].split(" ")
    f.close()

    csp = State(rows, cols, listOfObstacles, numOfEachEnemies)
    return csp

class Assignment:

    def __init__(self, maxNumOfEachEnemy) -> None:
        # numOfEachEnemies : King, Queen, Bishop, Rook, Knight
        self.maxNumOfEachEnemy = maxNumOfEachEnemy
        self.currentNumOfEachEnemy = [0, ] * len(maxNumOfEachEnemy)
        self.assignment = {}
    
    def isComplete(self) -> bool:
        for i in range(len(Piece.enemyTypes)):
            if self.currentNumOfEachEnemy[i] != self.maxNumOfEachEnemy[i]:
                return False
        return True
    
    def addAssignment(self, enemyType: str, position: tuple):
        self.currentNumOfEachEnemy[Piece.enemyTypes.index(enemyType)] += 1
        self.assignment[position] = enemyType
    
    def removeAssignment(self, enemyType: str, position: tuple):
        self.currentNumOfEachEnemy[Piece.enemyTypes.index(enemyType)] -= 1
        del self.assignment[position]
    
    def isInAssignment(self, position: tuple):
        return position in list(self.assignment.keys())

def selectUnassignedVariable(csp: State, assignment: Assignment):
    minNumOfUnassignedVariable = 5
    minx, miny = 0, 0
    for x in range(csp.cols):
        for y in range(csp.rows):
            if assignment.isInAssignment((x, y)):
                continue
            if len(csp.board.possibleEnemyTypes[x][y]) < minNumOfUnassignedVariable:
                minNumOfUnassignedVariable = len(csp.board.possibleEnemyTypes[x][y])
                minx, miny = x, y
                if minNumOfUnassignedVariable == 1:
                    break

    return (minx, miny)

def orderDomainValues(csp: State, variable: tuple, assignment: Assignment):

    result = []
    x, y = variable
    sizeOfResult = len(csp.board.possibleEnemyTypes[x][y])
    assignedPos = assignment.assignment.keys()
    for pieceTypeID in csp.board.possibleEnemyTypes[x][y]:
        if csp.board.maxNumOfEachEnemy[pieceTypeID] == csp.board.currentNumOfEachEnemy[pieceTypeID]:
            continue
        type = Piece.enemyTypes[pieceTypeID]
        threatened_count = 0
        if type == "Knight":
            for twoSteps in [-2, 2]:
                for oneStep in [-1, 1]:
                    if csp.board.isWithinBoard(x + twoSteps, y+oneStep) or (
                        not (x + twoSteps, y+oneStep) in assignedPos
                    ):
                        threatened_count += 1

                    if csp.board.isWithinBoard(x + oneStep, y+twoSteps) or (
                        not (x + oneStep, y+twoSteps) in assignedPos
                    ):
                        threatened_count += 1
        else:
            transModel = pieceMovementModel(
                csp.board, x, y, Piece.movement[type])
            for possibleX, possibleY in transModel.getAllPossibleNewPos():
                if not (possibleX, possibleY) in assignedPos:
                    threatened_count += 1
        heapq.heappush(result, (threatened_count, type))

    return heapq.nlargest(sizeOfResult, result)

def backTrack(csp: State, assignment: Assignment):
    if assignment.isComplete():
        return assignment
    variable = selectUnassignedVariable(csp, assignment)
    print("pos:", variable)
    for count, value in orderDomainValues(csp, variable, assignment):
        print("piece type:", value)
        assignment.addAssignment(value, variable)
        csp.setAssignment(assignment.assignment)
        inference = csp.inference(value, variable)
        print("result:", inference)
        if inference != "FAILURE":
            result = backTrack(csp, assignment)
            if result != "FAILURE":
                return result
        assignment.removeAssignment(value, variable)
        csp.setAssignment(assignment.assignment)
    return "FAILURE"



def search(testfile):
    csp = parser(testfile)

    return backTrack(csp, Assignment(csp.numOfEachEnemies))
    


### DO NOT EDIT/REMOVE THE FUNCTION HEADER BELOW###
# To return: Goal State which is a dictionary containing a mapping of the position of the grid to the chess piece type.
# Chess Pieces: King, Queen, Knight, Bishop, Rook (First letter capitalized)
# Positions: Tuple. (column (String format), row (Int)). Example: ('a', 0)

# Goal State to return example: {('a', 0) : Queen, ('d', 10) : Knight, ('g', 25) : Rook}
def run_CSP():
    # You can code in here but you cannot remove this function or change the return type
    testfile = sys.argv[1] #Do not remove. This is your input testfile.

    goalState = search(testfile)
    return goalState #Format to be returned

print(run_CSP())