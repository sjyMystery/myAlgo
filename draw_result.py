from myalgo.drawer.resultDrawer import ResultDrawer
from myalgo.optimizer.results import ResultManager

instruments = ['AUDCAD', 'AUDCHF', 'AUDJPY', "AUDNZD", "CADCHF", "EURAUD", "EURCHF",
               "EURGBP",
               "EURJPY",
               "EURUSD",
               "GBPCHF",
               "GBPJPY",
               "GBPNZD",
               "GBPUSD",
               "NZDCAD",
               "NZDCHF",
               "NZDJPY",
               "NZDUSD",
               "USDCAD",
               "USDCHF",
               "USDJPY"]
contour = True

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.

    for instrument in instruments:
        print(f'drawing {instrument}')
        # now draw curves
        result = ResultManager('BackTestStrategy', file_name=f"result_data/{instrument}.sqlite")
        data = result.load()

        drawer = ResultDrawer(data)
        if contour:
            drawer.draw_contours(f'./result_image/{instrument}-contour.png')
        else:
            drawer.draw_lines(f'./result_image/{instrument}-line.png')
