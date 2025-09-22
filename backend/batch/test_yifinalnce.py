import yfinance as yf


def func() -> None:
    print(yf.Ticker("7203.T").info)


if __name__ == "__main__":
    func()
