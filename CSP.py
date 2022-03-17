import sys
import random
import heapq
# from time import time
import itertools
# import numpy as np

class Piece:

    enemyTypes = ["King", "Queen", "Bishop", "Rook", "Knight"]

    movement = {"King": [(1, 1, 1), (1, 0, 1), (1, -1, 1), (0, -1, 1), (-1, -1, 1), (-1, 0, 1), (-1, 1, 1), (0, 1, 1)],
                "Rook": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0)],
                "Bishop": [(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Queen": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0), (1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Knight": [(2, 1, 1), (2, -1, 1), (1, 2, 1), (1, -2, 1), (-2, 1, 1), (-2, -1, 1), (-1, 2, 1), (-1, -2, 1)],
                "Obstacle": [],
                "Empty": [],
                }

    def __init__(self, pieceType: str) -> None:
        self.type = pieceType

    def possibleMovement(enemyType = None):
        return Piece.movement[enemyType]


class Board:


    def __init__(self, cols: int, rows: int, listOfObstacles, maxNumOfEachEnemy) -> None:
        self.enemyPos = {}  # (x, y) -> Enemy type
        self.numberOfEachEnemy = {
            "King": 0, 
            "Queen": 0, 
            "Bishop": 0, 
            "Rook": 0, 
            "Knight": 0
        } 
        self.obstaclePos = set() # to keep track which position to skip

        self.board_size_x = cols
        self.board_size_y = rows
        self.maxNumOfEachEnemy = maxNumOfEachEnemy
        
        # 2D array to store possible enemy types at the particular position
        self.possibleEnemyTypes = []
        sample = set(self.numberOfEachEnemy.keys())
        for i in range(cols):
            self.possibleEnemyTypes.append([])
            for j in range(rows):
                self.possibleEnemyTypes[i].append(sample.copy())
        
        # add the obstacles
        for x, y in listOfObstacles:
            self.addObstaclePiece(x, y)

    def isBlocked(self, x: int, y:int) -> bool:
        '''Occupied by enemy piece or by obstacle piece'''
        return ((x, y) in self.obstaclePos) or ((x, y) in self.enemyPos.keys())

    def isOccupiedByEnemyPiece(self, x: int, y: int) -> bool:
        return (x, y) in self.enemyPos.keys()

    def addEnemyPiece(self, pieceType: str, x: int, y: int) -> None:
        self.enemyPos[(x, y)] = pieceType
        self.possibleEnemyTypes[x][y] = {pieceType}
        self.numberOfEachEnemy[pieceType] += 1
        
        # mark all threatened position's available pieces as []
        transitionModel = pieceMovementModel(self, x, y, pieceType)
        for threatenedX, threatenedY in transitionModel.getAllPossibleNewPos():
            self.possibleEnemyTypes[threatenedX][threatenedY] = set()

        # for all other pieces type, T, at the position, mark the threatened available pieces -T
        for otherType in Piece.enemyTypes:
            if otherType == pieceType:
                continue
            transitionModel = pieceMovementModel(self, x, y, otherType)
            for threatenedX, threatenedY in transitionModel.getAllPossibleNewPos():
                self.possibleEnemyTypes[threatenedX][threatenedY].discard(otherType)
        
    def addObstaclePiece(self, x: int, y: int) -> None:
        self.obstaclePos.add((x, y))
        self.possibleEnemyTypes[x][y] = set()

    def isWithinBoard(self, x, y) -> bool:
        if (0 > x or x >= self.board_size_x) or (0 > y or y >= self.board_size_y):
            return False
        return True


class pieceMovementModel():

    def __init__(self, board: Board, x: int, y: int, pieceType: str):
        self.x = x
        self.y = y
        self.board = board
        self.movements = Piece.movement[pieceType]

    def moveToDirection(self, x_change: int, y_change: int):
        new_x = self.x + x_change
        new_y = self.y + y_change
        return (new_x, new_y)

    def __getAllPossibleMovementToDirection(self, x_change: int, y_change: int, max_steps=0):
        '''Get all the positions that the piece can move to, including position that are being threatened by other pieces'''
        if max_steps == 0:
            max_steps = max(self.board.board_size_x, self.board.board_size_y)
        steps = []
        for i in range(max_steps):
            new_pos = self.moveToDirection((i+1) * x_change, (i+1) * y_change)
            if (not self.board.isWithinBoard(new_pos[0], new_pos[1])):
                break
            if self.board.isBlocked(new_pos[0], new_pos[1]):
                # in the context of CSP, the piece violates constraints
                # print("ERROR: CONSTRAINT VIOLATION", new_pos[0], new_pos[1])
                steps.append(new_pos)
                break
            steps.append(new_pos)
        return steps

    def getAllPossibleNewPos(self):
        steps = []
        for movement in self.movements:
            xChange, yChange, maxSteps = movement
            steps.extend(self.__getAllPossibleMovementToDirection(xChange, yChange, maxSteps))
        return steps

class State:

    def __init__(self, rows, cols, listOfObstacles, maxNumberOfEachEnemies) -> None:
        self.board = Board(cols, rows, listOfObstacles, maxNumberOfEachEnemies)
        self.rows = rows
        self.cols = cols
        self.listOfObstacles = listOfObstacles
        self.maxNumberOfEachEnemies = maxNumberOfEachEnemies
        
    def setAssignment(self, assignment: dict):
        self.board = Board(self.cols, self.rows, self.listOfObstacles, self.maxNumberOfEachEnemies)
        for pos in assignment.keys():
            self.board.addEnemyPiece(assignment[pos], pos[0], pos[1])
    
    def updateAssignment(self, enemyType: str, position: tuple):
        self.board.addEnemyPiece(enemyType, position[0], position[1])

    def inference(self) -> bool:
        # print(np.array([[len(x) for x in row] for row in self.board.possibleEnemyTypes]))
        remainingPiecesCount = sum([self.maxNumberOfEachEnemies[pieceType] for pieceType in Piece.enemyTypes]) - len(self.board.enemyPos)
        # print("remaining pieces", remainingPiecesCount)

        remainingPositionsCount = 0
        for x in range(self.cols):
            for y in range(self.rows):
                if self.board.isBlocked(x, y):
                    continue
                if len(self.board.possibleEnemyTypes[x][y]) != 0:
                    remainingPositionsCount += 1
                    if remainingPositionsCount >= remainingPiecesCount:
                        return True
        return False

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
    numOfEachEnemiesList = input().split(":")[1].split(" ")
    numOfEachEnemies = {
            "King": int(numOfEachEnemiesList[0]), 
            "Queen": int(numOfEachEnemiesList[1]), 
            "Bishop": int(numOfEachEnemiesList[2]), 
            "Rook": int(numOfEachEnemiesList[3]), 
            "Knight": int(numOfEachEnemiesList[4])
        } 
    f.close()

    csp = State(rows, cols, listOfObstacles, numOfEachEnemies)
    return csp

class Assignment:

    def __init__(self, maxNumOfEachEnemy) -> None:
        # numOfEachEnemies : King, Queen, Bishop, Rook, Knight
        self.maxNumOfEachEnemy = maxNumOfEachEnemy
        self.currentNumOfEachEnemy = {
            "King": 0, 
            "Queen": 0, 
            "Bishop": 0, 
            "Rook": 0, 
            "Knight": 0
        } 
        self.assignment = {}
    
    def isComplete(self) -> bool:
        for enemyType in Piece.enemyTypes:
            if self.currentNumOfEachEnemy[enemyType] != self.maxNumOfEachEnemy[enemyType]:
                return False
        return True
    
    def addAssignment(self, enemyType: str, position: tuple):
        self.currentNumOfEachEnemy[enemyType] += 1
        self.assignment[position] = enemyType
    
    def removeAssignment(self, enemyType: str, position: tuple):
        self.currentNumOfEachEnemy[enemyType] -= 1
        del self.assignment[position]
    
    def isInAssignment(self, position: tuple):
        return position in list(self.assignment.keys())

def selectUnassignedVariable(csp: State, assignment: Assignment):
    '''Select the piece type that has the least number of available positions'''

    remainingTypes = []
    # for all remaining piece types that are yet to be assigned
    for pieceType in Piece.enemyTypes:
        if assignment.currentNumOfEachEnemy[pieceType] == assignment.maxNumOfEachEnemy[pieceType]:
            continue
        remainingTypes.append(pieceType)
    if len(remainingTypes) == 1:
        return remainingTypes[0]
    minimumCount = csp.cols * csp.rows
    minimumType = None
    for pieceType in remainingTypes:
        # count the number of positions that has this piece type 
        count = 0
        
        skip = False
        for x, y in list(itertools.product(range(csp.cols), range(csp.rows))):
            if pieceType in csp.board.possibleEnemyTypes[x][y]:
                count += 1
                if count > minimumCount:
                    skip = True
                    break
        
        if skip:
            continue

        if count == 1:
            return pieceType
        
        minimumType = pieceType
        minimumCount = count
    return minimumType

def orderDomainValues(csp: State, pieceType: str, assignment: Assignment):
    '''Order the positions in increasing number of positions threatened by the piece'''

    result = []
    # for all position
    for x, y in list(itertools.product(range(csp.cols), range(csp.rows))):
        if (x, y) in csp.board.enemyPos or (
            pieceType not in csp.board.possibleEnemyTypes[x][y]):
            continue
        
        transModel = pieceMovementModel(csp.board, x, y, pieceType)
        # add the number of positions threatened by the piece at that position to the list
        result.append((len(transModel.getAllPossibleNewPos()), (x, y)))

    result.sort()
    return result

def backTrack(csp: State, assignment: Assignment):
    # print("current assignment", assignment.assignment)
    # input()
    # print("-"*80)
    enemyType = selectUnassignedVariable(csp, assignment)
    for _, position in orderDomainValues(csp, enemyType, assignment):
        assignment.addAssignment(enemyType, position)
        csp.updateAssignment(enemyType, position)
        
        if assignment.isComplete():
            # print(assignment.assignment)
            return assignment.assignment

        inference = csp.inference()
        if inference != False:
            result = backTrack(csp, assignment)
            if result != "FAILURE":
                return result
        assignment.removeAssignment(enemyType, position)
        csp.setAssignment(assignment.assignment)
        # print("Backtrack to", assignment.assignment)
    return "FAILURE"



def search(testfile):
    csp = parser(testfile)

    # testAssignment = Assignment(csp.maxNumberOfEachEnemies)
    # testAssignment.addAssignment("Queen", (0, 0))
    # testAssignment.addAssignment("Queen", (1, 6))
    # testAssignment.addAssignment("Queen", (2, 4))
    # testAssignment.addAssignment("Queen", (3, 7))
    # testAssignment.addAssignment("Queen", (4, 1))
    # testAssignment.addAssignment("Queen", (5, 3))
    # testAssignment.addAssignment("Queen", (6, 5))
    # testAssignment.addAssignment("Queen", (7, 2))
    # csp.setAssignment(testAssignment.assignment)

    # return backTrack(csp, testAssignment)
    return backTrack(csp, Assignment(csp.maxNumberOfEachEnemies))
    


### DO NOT EDIT/REMOVE THE FUNCTION HEADER BELOW###
# To return: Goal State which is a dictionary containing a mapping of the position of the grid to the chess piece type.
# Chess Pieces: King, Queen, Knight, Bishop, Rook (First letter capitalized)
# Positions: Tuple. (column (String format), row (Int)). Example: ('a', 0)

# Goal State to return example: {('a', 0) : Queen, ('d', 10) : Knight, ('g', 25) : Rook}
def run_CSP():
    # You can code in here but you cannot remove this function or change the return type
    testfile = sys.argv[1] #Do not remove. This is your input testfile.
    rawResult = search(testfile)

    goalState = {}
    for pos in rawResult.keys():
        goalState[XYtoPos(pos)] = rawResult[pos]
    
    return goalState #Format to be returned

# startTime = time()
# print(run_CSP())
# print(time() - startTime)