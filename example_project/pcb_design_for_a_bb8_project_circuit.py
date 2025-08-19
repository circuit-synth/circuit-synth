from circuit_synth import *

@circuit(name="BB8_Control_Board")
def main():
    '''
    PCB design for a BB-8 project control board.
    Features an ESP32 for wireless control and an STM32F4 for motor control and sensor processing.
    Includes power management, USB-C for programming/power, and LED indicators.
    '''

    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_vbus = Net('USB_VBUS')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')

    # --- Power Management ---

    # USB-C Connector
    usb_c_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_USB2.0_16P_TopMount_Horizontal"
    )
    usb_c_conn[A1] += gnd
    usb_c_conn[A4] += usb_vbus
    usb_c_conn[A5] += usb_dp
    usb_c_conn[A6] += usb_dm
    usb_c_conn[A8] += gnd
    usb_c_conn[A9] += usb_vbus
    usb_c_conn[A12] += usb_dp
    usb_c_conn[A13] += usb_dm
    usb_c_conn[A16] += gnd
    usb_c_conn[B1] += gnd
    usb_c_conn[B4] += usb_vbus
    usb_c_conn[B5] += usb_dp
    usb_c_conn[B6] += usb_dm
    usb_c_conn[B8] += gnd
    usb_c_conn[B9] += usb_vbus
    usb_c_conn[B12] += usb_dp
    usb_c_conn[B13] += usb_dm
    usb_c_conn[B16] += gnd

    # 5V to 3.3V Linear Regulator (AMS1117-3.3)
    reg_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    reg_3v3[1] += gnd      # GND
    reg_3v3[2] += vcc_3v3  # VOUT
    reg_3v3[3] += usb_vbus # VIN

    # Input decoupling for 3.3V regulator
    c_reg_in_10u = Component(symbol="Device:C", ref="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
    c_reg_in_10u.value = "10uF"
    c_reg_in_10u[1] += usb_vbus
    c_reg_in_10u[2] += gnd

    c_reg_in_100n = Component(symbol="Device:C", ref="C2", footprint="Capacitor_SMD:C_0603_1608Metric")
    c_reg_in_100n.value = "100nF"
    c_reg_in_100n[1] += usb_vbus
    c_reg_in_100n[2] += gnd

    # Output decoupling for 3.3V regulator
    c_reg_out_10u = Component(symbol="Device:C", ref="C3", footprint="Capacitor_SMD:C_0603_1608Metric")
    c_reg_out_10u.value = "10uF"
    c_reg_out_10u[1] += vcc_3v3
    c_reg_out_10u[2] += gnd

    c_reg_out_100n = Component(symbol="Device:C", ref="C4", footprint="Capacitor_SMD:C_0603_1608Metric")
    c_reg_out_100n.value = "100nF"
    c_reg_out_100n[1] += vcc_3v3
    c_reg_out_100n[2] += gnd

    # --- Microcontrollers ---

    # ESP32-S3-MINI-1 (for Wi-Fi/Bluetooth communication)
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U2",
        footprint="RF_Module:ESP32-S2-MINI-1" # Footprint is compatible for MINI-1 series
    )
    esp32[1] += gnd      # GND
    esp32[2] += vcc_3v3  # VCC
    esp32[3] += Net('ESP_GPIO1')
    esp32[4] += Net('ESP_GPIO2')
    esp32[5] += Net('ESP_GPIO3')
    esp32[6] += Net('ESP_GPIO4')
    esp32[7] += Net('ESP_GPIO5')
    esp32[8] += Net('ESP_GPIO6')
    esp32[9] += Net('ESP_GPIO7')
    esp32[10] += Net('ESP_GPIO8')
    esp32[11] += Net('ESP_GPIO9')
    esp32[12] += Net('ESP_GPIO10')
    esp32[13] += Net('ESP_GPIO11')
    esp32[14] += Net('ESP_GPIO12')
    esp32[15] += Net('ESP_GPIO13')
    esp32[16] += Net('ESP_GPIO14')
    esp32[17] += Net('ESP_GPIO15')
    esp32[18] += Net('ESP_GPIO16')
    esp32[19] += Net('ESP_GPIO17')
    esp32[20] += Net('ESP_GPIO18')
    esp32[21] += Net('ESP_GPIO19')
    esp32[22] += Net('ESP_GPIO20')
    esp32[23] += Net('ESP_GPIO21')
    esp32[24] += Net('ESP_GPIO22')
    esp32[25] += Net('ESP_GPIO23')
    esp32[26] += Net('ESP_GPIO24')
    esp32[27] += Net('ESP_GPIO25')
    esp32[28] += Net('ESP_GPIO26')
    esp32[29] += Net('ESP_GPIO27')
    esp32[30] += Net('ESP_GPIO28')
    esp32[31] += Net('ESP_GPIO29')
    esp32[32] += Net('ESP_GPIO30')
    esp32[33] += Net('ESP_GPIO31')
    esp32[34] += Net('ESP_GPIO32')
    esp32[35] += Net('ESP_GPIO33')
    esp32[36] += Net('ESP_GPIO34')
    esp32[37] += Net('ESP_GPIO35')
    esp32[38] += Net('ESP_GPIO36')
    esp32[39] += Net('ESP_GPIO37')
    esp32[40] += Net('ESP_GPIO38')
    esp32[41] += Net('ESP_GPIO39')
    esp32[42] += Net('ESP_GPIO40')
    esp32[43] += Net('ESP_GPIO41')
    esp32[44] += Net('ESP_GPIO42')
    esp32[45] += Net('ESP_GPIO43')
    esp32[46] += Net('ESP_GPIO44')
    esp32[47] += Net('ESP_GPIO45')
    esp32[48] += Net('ESP_GPIO46')
    esp32[49] += Net('ESP_GPIO47')
    esp32[50] += Net('ESP_GPIO48')
    esp32[51] += Net('ESP_GPIO49')
    esp32[52] += Net('ESP_GPIO50')
    esp32[53] += Net('ESP_GPIO51')
    esp32[54] += Net('ESP_GPIO52')
    esp32[55] += Net('ESP_GPIO53')
    esp32[56] += Net('ESP_GPIO54')
    esp32[57] += Net('ESP_GPIO55')
    esp32[58] += Net('ESP_GPIO56')
    esp32[59] += Net('ESP_GPIO57')
    esp32[60] += Net('ESP_GPIO58')
    esp32[61] += Net('ESP_GPIO59')
    esp32[62] += Net('ESP_GPIO60')
    esp32[63] += Net('ESP_GPIO61')
    esp32[64] += Net('ESP_GPIO62')
    esp32[65] += Net('ESP_GPIO63')
    esp32[66] += Net('ESP_GPIO64')
    esp32[67] += Net('ESP_GPIO65')
    esp32[68] += Net('ESP_GPIO66')
    esp32[69] += Net('ESP_GPIO67')
    esp32[70] += Net('ESP_GPIO68')
    esp32[71] += Net('ESP_GPIO69')
    esp32[72] += Net('ESP_GPIO70')
    esp32[73] += Net('ESP_GPIO71')
    esp32[74] += Net('ESP_GPIO72')
    esp32[75] += Net('ESP_GPIO73')
    esp32[76] += Net('ESP_GPIO74')
    esp32[77] += Net('ESP_GPIO75')
    esp32[78] += Net('ESP_GPIO76')
    esp32[79] += Net('ESP_GPIO77')
    esp32[80] += Net('ESP_GPIO78')
    esp32[81] += Net('ESP_GPIO79')
    esp32[82] += Net('ESP_GPIO80')
    esp32[83] += Net('ESP_GPIO81')
    esp32[84] += Net('ESP_GPIO82')
    esp32[85] += Net('ESP_GPIO83')
    esp32[86] += Net('ESP_GPIO84')
    esp32[87] += Net('ESP_GPIO85')
    esp32[88] += Net('ESP_GPIO86')
    esp32[89] += Net('ESP_GPIO87')
    esp32[90] += Net('ESP_GPIO88')
    esp32[91] += Net('ESP_GPIO89')
    esp32[92] += Net('ESP_GPIO90')
    esp32[93] += Net('ESP_GPIO91')
    esp32[94] += Net('ESP_GPIO92')
    esp32[95] += Net('ESP_GPIO93')
    esp32[96] += Net('ESP_GPIO94')
    esp32[97] += Net('ESP_GPIO95')
    esp32[98] += Net('ESP_GPIO96')
    esp32[99] += Net('ESP_GPIO97')
    esp32[100] += Net('ESP_GPIO98')
    esp32[101] += Net('ESP_GPIO99')
    esp32[102] += Net('ESP_GPIO100')
    esp32[103] += Net('ESP_GPIO101')
    esp32[104] += Net('ESP_GPIO102')
    esp32[105] += Net('ESP_GPIO103')
    esp32[106] += Net('ESP_GPIO104')
    esp32[107] += Net('ESP_GPIO105')
    esp32[108] += Net('ESP_GPIO106')
    esp32[109] += Net('ESP_GPIO107')
    esp32[110] += Net('ESP_GPIO108')
    esp32[111] += Net('ESP_GPIO109')
    esp32[112] += Net('ESP_GPIO110')
    esp32[113] += Net('ESP_GPIO111')
    esp32[114] += Net('ESP_GPIO112')
    esp32[115] += Net('ESP_GPIO113')
    esp32[116] += Net('ESP_GPIO114')
    esp32[117] += Net('ESP_GPIO115')
    esp32[118] += Net('ESP_GPIO116')
    esp32[119] += Net('ESP_GPIO117')
    esp32[120] += Net('ESP_GPIO118')
    esp32[121] += Net('ESP_GPIO119')
    esp32[122] += Net('ESP_GPIO120')
    esp32[123] += Net('ESP_GPIO121')
    esp32[124] += Net('ESP_GPIO122')
    esp32[125] += Net('ESP_GPIO123')
    esp32[126] += Net('ESP_GPIO124')
    esp32[127] += Net('ESP_GPIO125')
    esp32[128] += Net('ESP_GPIO126')
    esp32[129] += Net('ESP_GPIO127')
    esp32[130] += Net('ESP_GPIO128')
    esp32[131] += Net('ESP_GPIO129')
    esp32[132] += Net('ESP_GPIO130')
    esp32[133] += Net('ESP_GPIO131')
    esp32[134] += Net('ESP_GPIO132')
    esp32[135] += Net('ESP_GPIO133')
    esp32[136] += Net('ESP_GPIO134')
    esp32[137] += Net('ESP_GPIO135')
    esp32[138] += Net('ESP_GPIO136')
    esp32[139] += Net('ESP_GPIO137')
    esp32[140] += Net('ESP_GPIO138')
    esp32[141] += Net('ESP_GPIO139')
    esp32[142] += Net('ESP_GPIO140')
    esp32[143] += Net('ESP_GPIO141')
    esp32[144] += Net('ESP_GPIO142')
    esp32[145] += Net('ESP_GPIO143')
    esp32[146] += Net('ESP_GPIO144')
    esp32[147] += Net('ESP_GPIO145')
    esp32[148] += Net('ESP_GPIO146')
    esp32[149] += Net('ESP_GPIO147')
    esp32[150] += Net('ESP_GPIO148')
    esp32[151] += Net('ESP_GPIO149')
    esp32[152] += Net('ESP_GPIO150')
    esp32[153] += Net('ESP_GPIO151')
    esp32[154] += Net('ESP_GPIO152')
    esp32[15