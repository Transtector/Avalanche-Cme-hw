import stpm34_2

print hex(stpm34_2.signal['V1_RMS']['address'])
print hex(stpm34_2.signal['V1_RMS']['mask'])

print hex(stpm34_2.signal['V2_RMS']['address'])
print hex(stpm34_2.signal['V2_RMS']['mask'])


print stpm34_2.defines.AEM_APPARENT_RMS_POWER
print stpm34_2.defines.AEM_APPARENT_VECTORIAL_POWER

print stpm34_2.defines.AEM

stpm34_2.passTest(stpm34_2.defines.AEM)


stpm34_2.writeRegister(stpm34_2.defines.AEM1, stpm34_2.defines.AEM_APPARENT_RMS_POWER)
stpm34_2.writeRegister(stpm34_2.defines.AEM2, stpm34_2.defines.AEM_APPARENT_VECTORIAL_POWER)
