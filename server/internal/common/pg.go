package common

import (
	"time"

	"github.com/jackc/pgx/v5/pgtype"
)

func StringToTime(input string) pgtype.Time {
	parsedTime, err := time.Parse("15:04", input)
	if err != nil {
		panic(err)
	}

	wakeUpTimeMicroseconds := int64(parsedTime.Hour()*3600+parsedTime.Minute()*60+parsedTime.Second()) * 1000000

	time := pgtype.Time{
		Microseconds: wakeUpTimeMicroseconds,
		Valid:        true,
	}
	return time
}

func TimeToString(pt pgtype.Time) string {
	t := time.Unix(0, pt.Microseconds*1000).UTC()
	return t.Format("15:04")
}

func NumericToFloat64(pn pgtype.Numeric) float64 {
	f8, err := pn.Float64Value()
	if err != nil {
		return 0.0
	}

	return f8.Float64
}

func Float64ToFloat32Slice(in []float64) []float32 {
	out := make([]float32, len(in))
	for i, v := range in {
		out[i] = float32(v)
	}
	return out
}

func ToFloat64(v interface{}) float64 {
	if v == nil {
		return 0.0
	}
	switch val := v.(type) {
	case float64:
		return val
	case float32:
		return float64(val)
	case int64:
		return float64(val)
	case pgtype.Numeric:
		return NumericToFloat64(val)
	default:
		return 0.0
	}
}
