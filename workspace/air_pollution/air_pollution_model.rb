# frozen_string_literal: true

NoSE::Model.new do
  (Entity 'Station' do
    ID     'StationID'
    String 'StationName', 20
    String 'RegionName', 20
  end) * 1

  (Entity 'Pollutant' do
    ID     'PollutantID'
    String 'PollutantName', 10
    String 'Unit', 10
  end) * 11

  (Entity 'MonthlyMeasurement' do
    ID     'MeasurementID'
    Date   'Month'
    Float  'AverageValue'
    String 'Note', 50
  end) * 55

  HasOne 'station', 'measurements',
         {'MonthlyMeasurement' => 'Station'}

  HasOne 'pollutant', 'measurements',
         {'MonthlyMeasurement' => 'Pollutant'}
end

