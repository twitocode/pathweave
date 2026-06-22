package main

import (
	"fmt"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/twitocode/pathweave/go-api/internal/common"
)

func main() {
	startTime := pgtype.Time{
		Valid:        true,
		Microseconds: 1_000_000 * 60 * 60 * 7,
	}

	endTime := pgtype.Time{
		Valid:        true,
		Microseconds: 1_000_000 * 60 * 60 * 14,
	}

	bits, _ := common.CreateDayMask(startTime, endTime)

	for i := 0; i < 30; i++ {
		totalMinutes := 7*60 + (i * 30)
		hour := totalMinutes / 60
		minute := totalMinutes % 60

		status := "[ ] Free"
		if (bits & (1 << i)) != 0 {
			status = "[X] Busy"
		}

		fmt.Printf("%02d:%02d - %s\n", hour, minute, status)
	}
}
