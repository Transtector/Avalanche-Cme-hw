from stpm3x import STPM3X

system = {
    'loop_freq': 0.5,
    'sensors': [
        {   #sensor0
            'type': 'STPM34',
            'gpio_sync': 12,
            #SPI Interface
            'spi_bus': 0,
            'spi_device': 0,
            #ZCR/CLK Pin
            'ZCR_SEL': 0,
            'ZCR_EN': 0,
            #Tamper
            'TMP_TOL': 0,
            'TMP_EN': 0,
            #LED1 Settings
            'LED1OFF': True,
            'LPW1': 0,
            'LPS1': 0,
            'LCS1': 0,
            #LED2 Settings
            'LED2OFF': True,
            'LPW2': 0,
            'LPS2': 0,
            'LCS2': 0,
            #System Settings
            'EN_CUM': False,
            'REF_FREQ': STPM3X.REF_FREQ_60HZ,
            #Primary Channel Settings
            'GAIN1': STPM3X.GAIN_X2,
            'CLRSS1': False,
            'ENVREF1': True,
            'TC1': STPM3X.TEMP_COEF_ZERO,
            'AEM1': STPM3X.AEM_APPARENT_RMS_POWER,
            'APM1': STPM3X.APM_FUNDAMENTAL_POWER,
            'BHPFV1': True,
            'BHPFC1': True,
            'ROC1': False,
            'voltage_swell_threshold': 1023,
            'voltage_sag_threshold': 0,
            'current_swell_threshold': 1023,
            'rms_upper_threshold': 4095,
            'rms_lower_threshold': 4095,
            #Secondary Channel Settings 
            'GAIN2': STPM3X.GAIN_X2,
            'CLRSS2': False,
            'ENVREF2': True,
            'TC2': STPM3X.TEMP_COEF_ZERO,
            'AEM2': STPM3X.AEM_APPARENT_RMS_POWER,
            'APM2': STPM3X.APM_FUNDAMENTAL_POWER,
            'BHPFV2': True,
            'BHPFC2': True,
            'ROC2': False,
            'voltage_swell_threshold': 1023,
            'voltage_sag_threshold': 0,
            'current_swell_threshold': 1023,
            'rms_upper_threshold': 4095,
            'rms_lower_threshold': 4095,
        }, #end sensor0
        {   #sensor1
            'type': 'STPM34',
            'gpio_sync': 12,
            #SPI Interface
            'spi_bus': 0,
            'spi_device': 1,
            #ZCR/CLK Pin
            'ZCR_SEL': 0,
            'ZCR_EN': 0,
            #Tamper
            'TMP_TOL': 0,
            'TMP_EN': 0,
            #LED1 Settings
            'LED1OFF': True,
            'LPW1': 0,
            'LPS1': 0,
            'LCS1': 0,
            #LED2 Settings
            'LED2OFF': True,
            'LPW2': 0,
            'LPS2': 0,
            'LCS2': 0,
            #System Settings
            'EN_CUM': False,
            'REF_FREQ': STPM3X.REF_FREQ_60HZ,
            #Primary Channel Settings
            'GAIN1': STPM3X.GAIN_X2,
            'CLRSS1': False,
            'ENVREF1': True,
            'TC1': STPM3X.TEMP_COEF_ZERO,
            'AEM1': STPM3X.AEM_APPARENT_RMS_POWER,
            'APM1': STPM3X.APM_FUNDAMENTAL_POWER,
            'BHPFV1': True,
            'BHPFC1': True,
            'ROC1': False,
            'voltage_swell_threshold': 1023,
            'voltage_sag_threshold': 0,
            'current_swell_threshold': 1023,
            'rms_upper_threshold': 4095,
            'rms_lower_threshold': 4095,
            #Secondary Channel Settings 
            'GAIN2': STPM3X.GAIN_X2,
            'CLRSS2': False,
            'ENVREF2': True,
            'TC2': STPM3X.TEMP_COEF_ZERO,
            'AEM2': STPM3X.AEM_APPARENT_RMS_POWER,
            'APM2': STPM3X.APM_FUNDAMENTAL_POWER,
            'BHPFV2': True,
            'BHPFC2': True,
            'ROC2': False,
            'voltage_swell_threshold': 1023,
            'voltage_sag_threshold': 0,
            'current_swell_threshold': 1023,
            'rms_upper_threshold': 4095,
            'rms_lower_threshold': 4095,
        }, #end sensor1
    ] #end sensors[]
} #end system


    
