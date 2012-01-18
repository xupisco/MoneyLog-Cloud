new_file = open('moneylog_rawdata.txt', 'r')
ml_data = new_file.read()

salame = open('salame.txt', 'w')
salame.write(ml_data)
salame.close()


print ml_data