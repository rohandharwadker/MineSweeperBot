from random import randrange
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import sys


mode = ""
if ("--beginner" in sys.argv):
    mode = "beginner"
elif ("--intermediate" in sys.argv):
    mode = "intermediate"

URL = "https://minesweeperonline.com/#"+mode
DEF = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
BLUE = "\033[36m"
PURPLE = "\033[94m"
MAGENTA = "\033[35m"
VERSION = "1.1.0"
DEBUG_MODE = True

print("%s\n----------------\n MineSweeperBot\n     v%s\n----------------%s"%(BOLD,VERSION,DEF))

board_rows = 0
board_columns = 0
zero_tiles = []
took_action = False

def debug(string,c=DEF):
    if ("--debug" in sys.argv or DEBUG_MODE):
        print(c+str(string)+DEF)

print("\ninit...\n")
driver = webdriver.Chrome()
driver.get(URL)
action = ActionChains(driver)

def get_game_size():
    r = int(len(driver.find_elements(By.CLASS_NAME,"borderlr"))/2)
    c = int((len(driver.find_elements(By.CLASS_NAME,"bordertb")))/3)
    return (r,c)

def click_tile(x,y): # clicks a tile at x,y
    driver.find_elements(By.ID,"%s_%s"%(y,x))[0].click()

def flag_tile(x,y):
    tile = driver.find_elements(By.ID,"%s_%s"%(y,x))[0]
    action.context_click(tile)
    action.perform()

def id_to_coords(id):
    return id.split("_")

def get_tiles_around(_x,_y): # returns a list of selenium objects of all tiles around a tile
    tiles_around = []
    for i in range(3):
        x = i-1
        for j in range(3):
            y = j-1
            if not(_x+x < 1 or _y+y < 1 or _x+x > board_columns or _y+y > board_rows):
                html_tile = driver.find_elements(By.ID,"%s_%s"%(_y+y,_x+x))
                if (len(html_tile) > 0 and not (x == 0 and y == 0)):
                    tiles_around.append(html_tile[0])
    return tiles_around

def get_all_tiles(): # returns tiles and states in dict: { <row> : [{column : state},{column : state}], <row> : [{column : state},{column : state}], ... }
    global board_rows
    global board_columns
    global zero_tiles
    debug("finding tiles...")
    raw_tiles = driver.find_elements(By.CLASS_NAME,"square")
    zero_tiles = driver.find_elements(By.CLASS_NAME,"open0")
    for tile in zero_tiles:
        if (tile in raw_tiles):
            raw_tiles.remove(tile)
    debug("sorting tiles...")
    tiles = {}
    for i in range(board_rows):
        tiles[i+1] = []
    for tile in raw_tiles:
        if (not tile.get_attribute("style") == "display: none;"):
            y = int(tile.get_attribute("id").split("_")[0])
            x = int(tile.get_attribute("id").split("_")[-1])
            if ("bombflagged" in tile.get_attribute("class").split()):
                state = "flagged"
            elif ("blank" in tile.get_attribute("class").split()):
                state = "unopened"
            else:
                state = list(tile.get_attribute("class")[-1])[-1]
                tiles[y].append({x:state})
    debug("sorted tiles.")
    return tiles

def selenium_to_info(selenium_obj):
    y,x = id_to_coords(selenium_obj.get_attribute("id"))
    if ("bombflagged" in selenium_obj.get_attribute("class").split()):
        state = "flagged"
    elif ("blank" in selenium_obj.get_attribute("class").split()):
        state = "unopened"
    else:
        state = list(selenium_obj.get_attribute("class")[-1])[-1]
    return(x,y,state)

def info_to_selenium(x,y):
    return driver.find_elements(By.ID,"%s_%s"%(y,x))[0]

def get_opened_tiles(tiles): # get all the opened tiles and return as list of [ (x,y,number) ]
    opened_tiles = []
    for y,list_of_tiles in tiles.items():
        for tile in list_of_tiles:
            x = list(tile.keys())[0]
            try:
                num = int(list(tile.values())[0])
            except ValueError:
                debug("Damn- Hit a Mine. Game Over.",c=BOLD+RED)
                quit()
            if (num != 0):
                opened_tiles.append( (x,y,num) )
    return opened_tiles

def clear_tile(x,y,num):
    global took_action
    # Sort the surrounding tiles
    tile_breakdown = {
        "unopened":[],
        "flagged":[]
    }
    tiles_around = get_tiles_around(x,y) # list of selenium objects around
    for tile in tiles_around:
        tile_info = selenium_to_info(tile) # tile_info is now (x,y,state)
        try:
            tile_breakdown[tile_info[2]].append(tile)
        except KeyError:
            pass

    debug("\nEvaluating tile: (%s,%s) value: %s"%(x,y,num),c=MAGENTA)
    # Take action with sorted data
    if (len(tile_breakdown.get("unopened"))+len(tile_breakdown.get("flagged")) == num and num != 0):
        for i in range(len(tile_breakdown.get("unopened"))):
            tile = tile_breakdown.get("unopened")[i]
            tile_info = selenium_to_info(tile)
            flag_tile(tile_info[0],tile_info[1])
            debug("flagged mine at (%s,%s)"%(tile_info[0],tile_info[1]),c=RED)
            took_action = True
    if (len(tile_breakdown.get("flagged")) == num and num != 0 and len(tile_breakdown.get("unopened")) > 0):
        for i in range(len(tile_breakdown.get("unopened"))):
            tile = tile_breakdown.get("unopened")[i]
            tile_info = selenium_to_info(tile)
            tile.click()
            debug("cleared space at (%s,%s)"%(tile_info[0],tile_info[1]),c=GREEN)
            clear_tile(int(tile_info[0]),int(tile_info[1]),int(list(tile.get_attribute("class")[-1])[-1]))
            took_action = True
    debug("Finished Evaluating tile: (%s,%s)\n"%(x,y),c=PURPLE)
    return took_action

def guess_click(rows,columns,advanced=False): # randomly clicks a tile
    debug("guessing click...",c=YELLOW)
    guess_x,guess_y = randrange(1,columns),randrange(1,rows)
    tile = info_to_selenium(guess_x,guess_y)
    while not ("blank" in tile.get_attribute("class")):
        guess_x,guess_y = randrange(1,columns),randrange(1,rows)
        tile = info_to_selenium(guess_x,guess_y)
    click_tile(guess_x,guess_y)

def won_game():
    if (len(driver.find_elements(By.CLASS_NAME,"facewin")) > 0):
        debug("Successfully Cleared All Mines",c=BOLD+GREEN)
        return True
    return False

def sweep_those_mf_mines():
    global took_action
    all_tiles = get_all_tiles()
    opened_tiles = get_opened_tiles(all_tiles)
    action = False
    took_action = False
    for i in range(len(opened_tiles)):
        action = clear_tile(opened_tiles[i][0],opened_tiles[i][1],opened_tiles[i][2])
    if (not action):
        guess_click(board_rows,board_columns)
    if (not won_game()):
        sweep_those_mf_mines()

def main():
    global board_rows
    global board_columns

    board_rows,board_columns = get_game_size()
    debug("Starting %sx%s game..."%(board_columns,board_rows),c=GREEN)
    guess_click(board_rows,board_columns)
    sweep_those_mf_mines()

main()
debug("Finished Program - Press Enter to Quit")
input()
driver.quit()