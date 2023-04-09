import requests
import json
import datetime
import schedule
import time
from cryptography.fernet import Fernet

# yes yes i'm aware, this is not supposed to be secure. I just want to keep away the webhook scrapers
webhookAddress = b'gAAAAABkMhgbPRGmFYm1tlozOHQmpJtkxAeUOemH1jisypeEDw2kDeL93eiFgdcmP5R1nIO6WslvPQdzUCmVE5fM-mrIzJRWcZxpp7pMIVMma3xnKmfoaSGEq8xd-0E7VzbUmbNLEkfzsN093tw1AnnudSDJQwLZsOfbblHwFDYI2CVhJG4uzFF9XUdhxwkh3h3PcAXDYbI6r9t0H6Umn-ZRNoWQB_XTbcaLl9vZbuxn60tyQvEmvJQ='
webhookDecryptKey = b'jBZlLShpxzBd2Kofm6X_eb170iLQpPxgVnh_XfHD5Qw='
f = Fernet(webhookDecryptKey)
webhookAddress = f.decrypt(webhookAddress).decode("utf-8")

wordList = []
wordleId = 0

class DiscordWebhook:
    def __init__(self):
        global webhookAddress
        self.webhookUrl = webhookAddress
        self.webhookUsername = "WordleBot"
    def send(self, message):
        payload = {
            "username": self.webhookUsername,
            "content": message
        }
        requests.post(self.webhookUrl, json=payload)
    

class Guess:
    def __init__(self, guess, wordleSolution):
        self.guess = guess
        self.wordleSolution = wordleSolution
        self.correctness = self.computeGuessCorrectness()
    def getCorrectLetters(self):
        correctLetters = [''] * 5
        for i in range(len(self.correctness)):
            if self.correctness[i] == 'G':
                correctLetters[i] = self.guess[i]
        return correctLetters
    def getIncorrectLetters(self):
        incorrectLetters = []
        for i in range(len(self.correctness)):
            if self.correctness[i] == 'g':
                incorrectLetters.append(self.guess[i])
        return incorrectLetters
    def getWrongPlaceLetters(self):
        wrongPlaceLetters = [[]] * 5
        for i in range(len(self.correctness)):
            if self.correctness[i] == 'y':
                wrongPlaceLetters[i].append(self.guess[i])
        return wrongPlaceLetters
    def computeGuessCorrectness(self):
        # Check the correctness of the guess
        correctness = ""
        for i in range(len(self.guess)):
            if self.guess[i] == self.wordleSolution[i]:
                correctness += 'G'
            elif self.guess[i] in self.wordleSolution:
                correctness += 'y'
            else:
                correctness += 'g'
        return correctness
    def __str__(self):
        outputString = ""
        for i in range(len(self.correctness)):
            if self.correctness[i] == 'G':
                outputString += '🟩'
            elif self.correctness[i] == 'y':
                outputString += '🟨'
            elif self.correctness[i] == 'g':
                outputString += '⬛'
        return outputString
    
class WordleBotHistory:
    def __init__(self, wordleState):
        self.history = []
        self.wordleState = wordleState
    def addGuess(self, guess):
        self.history.append(guess)
    def __str__(self):
        outputString = ""
        for i in range(len(self.history)):
            outputString += self.history[i].__str__() + "\t" + "||" + self.history[i].guess + "||" + "\n"
        return outputString

class WordleState:
    def __init__(self):
        self.correctLetters = [''] * 5
        self.incorrectLetters = []
        self.wrongPlace = [[]] * 5
        self.guesses = 0
        self.maxGuesses = 6
    def addCorrectLetter(self, letter, position):
        self.correctLetters[position] = letter
    def addIncorrectLetter(self, letter):
        self.incorrectLetters.append(letter)
    def addWrongPlace(self, letter, position):
        self.wrongPlace[position].append(letter)
    def isSolved(self):
        for i in range(len(self.correctLetters)):
            if self.correctLetters[i] == '':
                return False
        return True
    def addGuess(self, guess):
        self.guesses += 1
        self.correctLetters = guess.getCorrectLetters()
        self.incorrectLetters += guess.getIncorrectLetters()
    def __str__(self):
        print("Guesses: " + self.guesses)
        print("Correct letters: " + self.correctLetters)
        print("Incorrect letters: " + self.incorrectLetters)
        print("Wrong place: " + self.wrongPlace)

def getWordleSolution():
    global wordleId
    # Get the wordle answer
    url = "https://www.nytimes.com/svc/wordle/v2/"
    # get today's date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    url += date + ".json"
    response = requests.get(url)
    data = json.loads(response.text)
    wordleId = data["days_since_launch"]
    return data["solution"]


def loadWordList():
    # Load the word list
    with open("wordlist.txt", "r") as wordListFile:
        for line in wordListFile:
            wordList.append(line.strip())

def pruneWordsWithIncorrectLetters(wordleState):
    global wordList
    newWordList = []
    for word in wordList:
        for i in range(len(word)):
            if word[i] in wordleState.incorrectLetters:
                break
        else:
            newWordList.append(word)
    wordList = newWordList

def pruneWordsWithNotCorrectLetters(wordleState):
    global wordList
    newWordList = []
    for word in wordList:
        shouldAddWord = True
        for i in range(len(word)):
            if wordleState.correctLetters[i] != '' and word[i] != wordleState.correctLetters[i]:
                shouldAddWord = False
                break
        if shouldAddWord:
            newWordList.append(word)
    wordList = newWordList

def pruneWordsWithWrongPlaceLetters(wordleState):
    global wordList
    newWordList = []
    for word in wordList:
        for i in range(len(word)):
            if word[i] in wordleState.wrongPlace[i]:
                break
        else:
            newWordList.append(word)
    wordList = newWordList


def pruneWordList(wordleState):
    # Prune the word list
    pruneWordsWithIncorrectLetters(wordleState)
    pruneWordsWithNotCorrectLetters(wordleState)
    pruneWordsWithWrongPlaceLetters(wordleState)

def getNextGuess():
    # Get the next guess
    return wordList[0]

def solveWithSolution(wordleSolution):
    # Solve the wordle
    wordleBotHistory = WordleBotHistory(WordleState())
    wordleState = wordleBotHistory.wordleState
    loadWordList()
    guess = "crane"
    isFirstWord = True
    while(wordleState.guesses < wordleState.maxGuesses and not wordleState.isSolved() and len(wordList) > 0):
        if not isFirstWord:
            guess = getNextGuess()
        isFirstWord = False
        guess = Guess(guess, wordleSolution)
        wordleState.addGuess(guess)
        wordleBotHistory.addGuess(guess)
        pruneWordList(wordleState)
    return wordleBotHistory

def constructResultString(wordleBotHistory):
    if wordleBotHistory.wordleState.guesses == wordleBotHistory.wordleState.maxGuesses:
        resultString = "Wordle " + str(wordleId) + " " + "x" + '/' + str(wordleBotHistory.wordleState.maxGuesses)
    else:    
        resultString = "Wordle " + str(wordleId) + " " + str(wordleBotHistory.wordleState.guesses) + '/' + str(wordleBotHistory.wordleState.maxGuesses)
    resultString += "\n\n"
    resultString += wordleBotHistory.__str__()
    return resultString

def printSolutionToDiscord(wordleBotHistory):
    DiscordWebhook().send(constructResultString(wordleBotHistory))

def main():
    print("Running main at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    wordleSolution = getWordleSolution()
    wordleBotHistory = solveWithSolution(wordleSolution)
    printSolutionToDiscord(wordleBotHistory)

if __name__ == "__main__":
    # run main every 24 hours at 12:00 PM
    main()
    schedule.every().day.at("12:00").do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)