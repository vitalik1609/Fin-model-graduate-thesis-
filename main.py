import json
import numpy_financial as np
from math import sqrt
import matplotlib.pyplot as plt


'''Открытие управляющего json файла'''
with open('network_actualized_for_forecast_removed_wells_var4.json', 'r') as fcc_file:
    fcc_data = json.load(fcc_file)
    #print(json.dumps(fcc_data, indent=4))

class OIL():
    '''Расчет нефти'''
    def __init__(self):
        '''переменные'''
        global V_oil, K_c, tax_rate, oil_cost, еxpenses, OCF, CapitalChanges, Amortization, OpEx, wellCost, wellCosts, npv_values, rate, value, timeLine, tubesLenghts, innerDiameters, roughness
        # V_oil - объем добытой нефти в год (в тоннах)
        V_oil = [71980, 68540, 84993, 73500, 87000, 94000, 73552, 81252, 56480, 72649, 66666, 69696, 66600, 65432, 77777, 77666, 76859, 75096, 67098, 90900, 98760, 87950, 76950, 89777, 70700, 96870, 77609, 96574, 88888, 88089,77667, 91300]
        tax_rate = 25299 # налоговая ставка Руб/тонну
        K_c = 0.2 #коэффициент для расчета НДПИ, Коэффициент, характеризующий уровень налогообложения нефти, добываемой на участках недр, в отношении которой исчисляется налог на дополнительный доход от добычи углеводородного сырья
        oil_cost = 40000  # стоимость нефти в рублях за тонну
        wellCost = 20000000  #Усредненная стоимость скважины
        wellCosts = {} #словарь со стоимостями скважин по id
        tubesLenghts = {} #словарь с длинами труб по id
        innerDiameters = {} #словарь с диаметрами труб по id
        roughness = {} #словарь с шероховатостями труб по id
        npv_values = [] #значения npv от времени
        rate = 0.1 # ставка дисконтирования для расчета NPV
        еxpenses = 5965 # ежегожные расходы (зарплаты, обслуживание техники и тд) на тонну добытой нефти, не хватает данных для расчета поэтому берем готовое число
        OpEx = [еxpenses*V_oil[i] for i in range(len(V_oil))]  #Операционные затраты
        OCF = [V_oil[i]*oil_cost - OpEx[i] - OIL.taxNDPI(self)[i] for i in range(len(V_oil))] #Операционная прибыль
        CapitalChanges = [77000000]*len(V_oil)
        Amortization = [55000000]*len(V_oil)
        value = [OIL.FCF1(self)[i]  for i in range(len(V_oil))] #денежные потоки для расчета NPV
        timeLine = [_ for _ in range(len(V_oil))] # линия времени

    tubeUnitCosts = {    #Удельные стоимости труб по id
        0: 20000,
        1: 15000,
        2: 17500,
        3: 23000,
        4: 14300,
        5: 30000,
        6: 25000,
        7: 12000,
        8: 29000,
        9: 24000,
        10: 16302,
        12: 27350
    }

    def taxNDPI(self):
        '''Возвращает налог ндпи по годам'''
        '''Объем добытой нефти за год*налоговая ставка*коэффициент'''
        ndpi = [V*tax_rate*K_c for V in V_oil]
        return ndpi

    def NPV(self, rate, value):
        '''расчет NPV (Наша собственная функция)'''
        '''Принимает ставку дисконтирования rate и денежные потоки списком value'''
        NPV = 0
        for t in range(len(value)):
            NPV += value[t]/(1+rate)**t
        return NPV


    def drawCharts(self):
        '''выводит график NPV и FCF от времени'''
        for i in range(len(value)):
            npv_values.append(np.npv(rate, value[:i]))  #заполняем список значений npv_values по годам
        plt.plot(timeLine, npv_values, label=r'$NPV$')  # график NPV от времени
        plt.plot(timeLine, [OIL.getCapEx(self)]*len(timeLine), label=r'$CapEx$') #выводим CapEx в первый год
        plt.plot(timeLine, OIL.FCF1(self), label=r'$FCF1$')   #график FCF1 от времени
        plt.plot(timeLine, OIL.FCF2(self), label=r'$FCF2$')  # график FCF1 от времени
        plt.xlabel('$Время, лет$')
        plt.ylabel('$Денежный поток$')
        plt.title('Зависимость NPV от времени')
        plt.grid(True)
        plt.legend(loc='best', fontsize=12)
        plt.show()
        plt.close()

    def getCapEx(self):
        '''Возвращает кап затраты'''
        return OIL.getTubeExpenses(self) + OIL.getWellExpenses(self)

    def EBITDA(self):
        '''расчет EBITDA (EBITDA=OCF+Амортизация основных и нематериальных активов)'''
        EBITDA = [ocf+amort for ocf, amort in zip(OCF, Amortization)]
        return EBITDA

    def FCF1(self):
        '''расчет FCF первым методом (FCF=OCF-CapEx)'''
        FCF1 = [OCF[0] - OIL.getCapEx(self)]+OCF[1:]
        return FCF1

    def FCF2(self):
        '''расчет FCF вторым методом (FCF=EBITDA-CapEx-текущий налог на прибыль-изменения в оборотном капитале)'''
        FCF2 = [OIL.EBITDA(self)[0]-OIL.taxNDPI(self)[0]-CapitalChanges[0]-OIL.getCapEx(self)]
        for year in range(1, len(V_oil)):
            FCF2.append(OIL.EBITDA(self)[year]-OIL.taxNDPI(self)[year]-CapitalChanges[year])
        return FCF2


    def getWellSum(self, pipes):
        '''возвращает кол-во скважин'''
        wellCounter = 0
        for pipe in pipes:
            if pipe["type"] == 'WELL':
                wellCounter += 1
        return wellCounter

    def setWellCosts(self, id, cost):
        '''Задает стоимость скважины по ее id'''
        wellCosts[id] = cost

    def getWellCosts(self, pipes):
        '''возвращает словарь со стоимостью скважин по их id'''
        '''если цена не задана, берется усредненная стоимость wellCost'''
        for pipe in pipes:
            if pipe["type"] == 'WELL' and pipe['id'] not in wellCosts.keys():
                wellCosts[pipe['id']] = wellCost
        sortedWellCosts = dict(sorted(wellCosts.items(), key=lambda x: x[0]))
        return sortedWellCosts

    def getWellExpenses(self):
        '''Возвращает капитальные затраты на скважины'''
        return sum(OIL.getWellCosts(self, fcc_data['pipes']).values()) #Сумма значений словаря со стоимостями скважин

    def getTubesLengths(self, pipes):
        '''возвращает словарь с длинами труб (м) по id'''
        for pipe in pipes:
            if pipe['type'] == 'TUBE':
                coordinates = [] #записываем координаты [x_0, y_0, x_1, y_1]
                id = pipe['id']
                for coord in pipe['profileHorDistanceMSpaceHeightM']:
                    coordinates.append(int(float(coord.split()[0])))
                    coordinates.append(int(float(coord.split()[1])))
                tubeLength = sqrt((coordinates[0] - coordinates[2]) ** 2 + (coordinates[1] - coordinates[3]) ** 2)
                tubesLenghts[id] = tubeLength
        return tubesLenghts

    def getInnerDiameter(self, pipes):
        '''возвращает диаметры труб (мм) по id'''
        for pipe in pipes:
            if pipe['type'] == 'TUBE' and 'innerDiameterMm' in pipe:
                innerDiameters[pipe['id']] = pipe['innerDiameterMm']
        return innerDiameters

    def getRoughness(self, pipes):
        '''возвращает шероховатости труб (мм) по id'''
        for pipe in pipes:
            if pipe['type'] == 'TUBE' and 'roughnessMm' in pipe:
                #print(pipe)
                roughness[pipe['id']] = pipe['roughnessMm']
        return roughness

    def getTubeExpenses(self):
        '''возвращает полную стоимость труб'''
        '''Умножает длины труб на их удельные стоимости и складывает'''
        return sum([x * y for x, y in zip(OIL.getTubesLengths(self, fcc_data["pipes"]).values(), OIL.tubeUnitCosts.values())])

N1 = OIL() #Объект класса OIL

'''Задаем стоимости скважин для примера'''
N1.setWellCosts(65, 35000000)
N1.setWellCosts(66, 40000000)
N1.setWellCosts(67, 45000000)
N1.setWellCosts(68, 50000000)
N1.setWellCosts(69, 55000000)
N1.setWellCosts(70, 60000000)
N1.setWellCosts(71, 65000000)
N1.setWellCosts(72, 70000000)
N1.setWellCosts(73, 75000000)
N1.setWellCosts(74, 80000000)
N1.setWellCosts(75, 85000000)
N1.setWellCosts(76, 90000000)
N1.setWellCosts(77, 95000000)
N1.setWellCosts(78, 100000000)

'''Выводим все имеющиеся данные'''
print('НДПИ:', N1.taxNDPI())
print('-'*200)
print('Количество скважин:', N1.getWellSum(fcc_data['pipes']))
print('-'*200)
print('Стоимости скважин по их id:', N1.getWellCosts(fcc_data['pipes']))
print('-'*200)
print('Кап. затраты на скважины:', N1.getWellExpenses())
print('-'*200)
print('Длины Труб по их id:', N1.getTubesLengths(fcc_data['pipes']))
print('-'*200)
print('Диаметры труб по их id:', N1.getInnerDiameter(fcc_data['pipes']))
print('-'*200)
print('Шероховатости труб по их id:', N1.getRoughness(fcc_data['pipes']))
print('-'*200)
print('Кап. затраты на трубы:', N1.getTubeExpenses())
print('-'*200)
print('NPV(задаем ставку дисконтирования и денежные потоки):', N1.NPV(rate, value))
print('-'*200)
print('FCF1(Задаем кэш от операций, учитываются НДПИ и кап затраты на трубы и скважины):', N1.FCF1())
print('-'*200)
print('FCF2(Задаем кэш от операций, учитываются НДПИ и кап затраты на трубы и скважины):', N1.FCF2())
print('-'*200)
print('CapEx: ', N1.getCapEx())
N1.drawCharts()


