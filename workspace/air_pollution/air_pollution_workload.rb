# frozen_string_literal: true

NoSE::Workload.new do
  Model '/work/air_pollution_model.rb'

  DefaultMix :default

  Group 'PollutantTrend', default: 40 do
    Q 'SELECT measurements.Month, measurements.AverageValue, ' \
      'measurements.Note FROM Pollutant.measurements ' \
      'WHERE Pollutant.PollutantID = ? ' \
      'ORDER BY measurements.Month'
  end

  Group 'StationMonthlySummary', default: 30 do
    Q 'SELECT measurements.AverageValue, pollutant.PollutantName, ' \
      'pollutant.Unit FROM Station.measurements.pollutant ' \
      'WHERE Station.StationID = ? AND measurements.Month = ?'
  end

  Group 'StationPollutantRange', default: 20 do
    Q 'SELECT measurements.Month, measurements.AverageValue FROM ' \
      'Station.measurements.pollutant WHERE Station.StationID = ? ' \
      'AND pollutant.PollutantID = ? AND measurements.Month >= ? ' \
      'AND measurements.Month <= ? ORDER BY measurements.Month'
  end

  Group 'InsertMonthlyMeasurement', default: 10 do
    Q 'INSERT INTO MonthlyMeasurement SET MeasurementID=?, Month=?, ' \
      'AverageValue=?, Note=? AND CONNECT TO station(?), pollutant(?)'
  end
end
